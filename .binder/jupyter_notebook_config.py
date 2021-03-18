# Traitlet configuration file for jupyter-notebook.

c.ServerProxy.servers = {
    'Thalassa': {
     #  'command': ['/home/jovyan/.openrefine/openrefine-2.8/refine', '-p', '{port}','-d','/home/jovyan/openrefine'],
        'command': ['panel', 'serve', 'poseidon_viz/Thalassa.ipynb' "--websocket-origin '*'",'-p', '{port}'],
        'port': 3333,
        'timeout': 120,
        'launcher_entry': {
            'enabled': True,
#           'icon_path': '/home/jovyan/.jupyter/open-refine-logo.svg',
            'title': 'Thalassa',
        },
    },
}
