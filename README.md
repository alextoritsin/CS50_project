# StockX — WSGI web-application based on Flask
#### Video Demo: 
#### In this application you can create your portfolio of stocks from US market, analise them, add to list and compare.

Before using you should get API key for IEX cloud service.
Instructions to get one you can find [here](https://cs50.harvard.edu/x/2021/psets/9/finance/#configuring).

Also in `__init__.py` you should provide appropriate SECRET_KEY for the Flask application.

In **templates** folder you can find all html templates for this repo. **Application** folder also provides 
main controller files: `models.py` with database tables, `views.py` with route functions, `forms.py` with classes for specific forms
and `__init__.py` as an executable module.

**Static** folder contains JavaScript code and CSS files, to supplement Boostrap classes.

Besides IEX Cloud service, this application implemented with free financial libraries: [yfinance](https://pypi.org/project/yfinance/) and [okama](https://github.com/mbk-dev/okama), so sometimes it may have some connection problems.



