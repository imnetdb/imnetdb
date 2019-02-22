all:
	@ echo "unit testing code"
	@ pytest -v \
		--ignore=test_clean.py \
		--cov ../imnetdb \
		--cov-report html:htmlcov \
		--cov-report term

clean:
	@ echo "cleaning up test environment"
	@ pytest -v test_clean.py

