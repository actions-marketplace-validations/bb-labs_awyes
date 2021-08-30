
type = patch

publish:
	poetry config http-basic.pypi trumanpurnell $(POETRY_PASSWORD)
	poetry version $(type)
	poetry build
	poetry publish

commit: 
	git add -A
	git commit -m "$(message)"
	git tag -am "$(message)" $(shell git describe --tags --abbrev=0 | awk -F. -v OFS=. '{$$NF++;print}')
	git push --follow-tags
