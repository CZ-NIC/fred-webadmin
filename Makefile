ROOT = ".."

.PHONY: check-css

check-css:
	stylelint www/**/*.css

check-all: check-css
