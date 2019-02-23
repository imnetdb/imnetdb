PACKAGE = $(python setup.py --name)

clean:
	@ $(MAKE) -C tests clean
	@ python setup.py clean
	@ rm -rf *.egg-info .pytest_cache
	@ find . -name '*.pyc' | xargs rm
