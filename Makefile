ROOT = ".."

.PHONY: check-css

check-css:
	stylelint www/**/*.css
