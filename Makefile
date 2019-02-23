PACKAGE = $(python setup.py --name)

clean:
	@ $(MAKE) -C tests clean
	@ python setup.py clean
	@ rm -rf *.egg-info .pytest_cache
	@ find . -name '*.pyc' | xargs rm

arangodb-start:
	(cd tests; docker-compose up -d)

arangodb-stop:
	(cd tests; docker-compose down)
