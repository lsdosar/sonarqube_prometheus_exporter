import time

import requests
from prometheus_client import Gauge, Info, start_http_server

import sonarqube
from sonarqube import SonarQubeClient

sonarqube_server = "http://192.168.3.101:9001"
sonarqube_token = "squ_af1e521e19aef5c5de1cb6df89adf3cbb3a9759e"
sonar = SonarQubeClient(sonarqube_url=sonarqube_server, token=sonarqube_token)

def get_stat(metrics):
    stats = []
    for metric in metrics:
        g = Gauge(metric['key'], metric['name'], ['project_key', 'domain'])
        stats.append({'gauge':g, 'metric':metric})
    return stats

def metric_types(metric_type, value):
    if metric_type in ['INT', 'FLOAT', 'PERCENT', 'MILLISEC']:
        return float(value)
    elif metric_type == 'BOOL':
        return bool(value)
    elif metric_type in ['STRING', 'DATA', 'LEVEL', 'DISTRIB', 'RATING', 'WORK_DUR']:
        return str(value)
    else:
        return value

def create_metrics(stats):
    g = stats['gauge']
    metric = stats['metric']
    projects = list(sonar.projects.search_projects())
    for p in projects:
        component = sonar.measures.get_component_with_specified_measures(component=p['key'], fields="metrics", metricKeys=metric['key'])
        measures = component['component']['measures']
        value = 0
        if len(measures) > 0:
            if 'value' in measures[0]:
                try:
                    value = metric_types(metric['type'], measures[0]['value'])
                except (KeyError, IndexError, NameError) as error:
                    value = -1
                    raise error
            elif 'periods' in measures[0]:
                try:
                    value = metric_types(metric['type'], measures[0]['periods'][0]['value'])
                except (KeyError, IndexError, NameError) as error:
                    value = -1
                    raise error
        if metric['type'] in ['INT', 'FLOAT', 'PERCENT', 'MILLISEC']:
            g.labels(
                project_key=p['key'], 
                domain=metric['domain'],
            ).set(value)

def main():
    metrics = list(sonar.metrics.search_metrics())
    stats = get_stat(metrics)
    start_http_server(8198)
    while True:
        for s in stats:
            create_metrics(s)
        time.sleep(5)

main()

