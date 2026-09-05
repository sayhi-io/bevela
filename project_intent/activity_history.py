"""Bounded process-local numeric observations, never durable intent or log history."""
import copy
import threading

from .activity import codex_activity

WINDOW_SECONDS = 900
MAX_POINTS = 180
MAX_SERIES = 2048


def enrollment_identity(scope, record):
    """A renewed lease may reuse history; another execution checkout may not."""
    telemetry = record.get('telemetry') or {}
    checkout = record.get('checkout') or {}
    if not isinstance(telemetry, dict) or not isinstance(telemetry.get('path'), str):
        return None
    return (scope, record['workstream'], record['session'],
            *(checkout.get(field) for field in ('host', 'root', 'repository_common_dir', 'branch')),
            telemetry.get('path'))


class ActivityHistory:
    def __init__(self):
        self._series = {}
        self._lock = threading.RLock()

    def prune(self, now):
        with self._lock:
            for key, item in list(self._series.items()):
                item['points'] = [p for p in item['points'] if now - WINDOW_SECONDS <= p['at']]
                if not item['points']:
                    del self._series[key]

    def observe(self, key, metric, now, epoch=None):
        """Retain already admitted points only. Freshness always comes from metric.

        The parser's first report after a new lease is null, so independent lease
        intervals cannot become a line across unassigned work. Numeric observations
        already seen survive a later bounded tail scan losing its predecessor.
        """
        with self._lock:
            self.prune(now)
            if key is None:
                return copy.deepcopy(metric)
            previous = self._series.get(key, {})
            points = {p['at']: p for p in previous.get('points', [])}
            for point in metric['points']:
                if now - WINDOW_SECONDS <= point['at'] <= now:
                    old = points.get(point['at'])
                    if old is None or old['value'] is None or old.get('_epoch') != epoch:
                        points[point['at']] = dict(copy.deepcopy(point), _epoch=epoch)
            retained = sorted(points.values(), key=lambda p: p['at'])[-MAX_POINTS:]
            result = copy.deepcopy(metric)
            result['points'] = []
            previous_epoch = None
            for point in retained:
                if point['at'] > now:
                    continue
                public = {k: v for k, v in point.items() if k != '_epoch'}
                if result['points'] and point['_epoch'] != previous_epoch:
                    public['break_before'] = True
                result['points'].append(public)
                previous_epoch = point['_epoch']
            result['history_coverage'] = 'Observed numeric samples only; 15m/180 points per execution source; process-local, cleared on service restart.'
            if retained:
                result['last_report_at'] = max(metric.get('last_report_at') or 0, result['points'][-1]['at']) if result['points'] else metric.get('last_report_at')
                self._series[key] = {'points': retained}
                while len(self._series) > MAX_SERIES:
                    oldest = min(self._series, key=lambda k: self._series[k]['points'][-1]['at'])
                    del self._series[oldest]
            return result

    def enrolled(self, scope, record, binding, now):
        # No binding means the lease is released/expired (or telemetry absent).
        # Crucially, do not reopen the log to reconstruct an ended lease.
        metric = codex_activity(binding or {'session': record['session']}, now)
        if binding is None:
            from .activity import timestamp
            metric['status'] = ('inactive' if record['status'] == 'inactive' else
                                'expired' if timestamp(record['expires_at']) <= now else 'not-connected')
        return self.observe(enrollment_identity(scope, record), metric, now, record['claimed_at'])
