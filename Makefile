# Simple makefile for common tasks

test:
	./run-tests

# Remove .pyc files
clean:
	find -type f -iname '*.pyc' -exec rm {} \;
	find -type f -iname '*.~*~' -exec rm {} \;
	rm -f *.bak
