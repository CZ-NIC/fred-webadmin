ROOT = ".."

.PHONY: check-css

check-css:
	stylelint fred_webadmin/www/**/*.css

check-all: check-css
