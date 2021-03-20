Large Scale Sea level visualizations of unstructured mesh data
===============================================================

This is a developmental prototype for visualizing large scale results of hydrodynamic simulations.

Thalassa is powered by

- [pyPoseidon](https://github.com/brey/pyPoseidon)

- [SCHISM](https://github.com/schism-dev/schism)

- [Panel](https://panel.holoviz.org/index.html)



## Instalation

### locally

Clone the repo

- option 1: 

	**Build using poetry and venv**
	
	Your system needs to have pip, python>=3.8, geos, gdal=3.2.1 and proj<8. 

	You can set one up with conda with 
	
	
	`python -m venv .venv
	source .venv/bin/activate
	poetry install`

	execute with 
	
	`pv serve --websocket-origin '*'`
	
	A webpage will open in your default browser 
	
- option 2:

	**Run using conda**
	
	create a new conda environment as
	
	`conda env create -f binder/environment.yml`
	
	Then
	
	- run the poseidon_viz/Thalassa.ipynb on jypyterlab/Notebook.
	
	- or launch it from the terminal 

	`panel serve poseidon_viz/Thalassa.ipynb --allow-websocket-origin=*`

	Then in your favorite browser visit
	
	`http://localhost:5006/Thalassa`
	

### Server deployment



## License
* The project is released under the EUPL v1.2 license.
