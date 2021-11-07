# StockX — WSGI web-application based on Flask

#### In this application you can create your portfolio of stocks from the US market, analise them, add to list and compare.

Before using it you should get the API key for IEX cloud service.
Instructions to get one you can find [here](https://cs50.harvard.edu/x/2021/psets/9/finance/#configuring).

Also in `__init__.py` you should provide appropriate SECRET_KEY for the Flask application.

In **templates** folder you can find all html templates for this repo. **Application** folder also provides 
main controller files: `models.py` with database tables, `views.py` with route functions, 
`forms.py` with classes for specific forms and `__init__.py` as an executable module.

**Static** folder contains JavaScript code and CSS files, to supplement Bootstrap classes.

Besides IEX Cloud service, this application implemented with free financial libraries: 
[yfinance](https://pypi.org/project/yfinance/) and [okama](https://github.com/mbk-dev/okama), so sometimes it may have some connection problems.

After registering and signing in, users will be redirected to the `/index` route. This route represents the assets, 
that the user has bought and amount of cash that was left. Be default amount of cash is equivalent to $10000 and
defined in `Users` class in `models.py`. 

Right before the start of the application in `/companies` route the list of companies will be build with the help
of okama library. Be default it consists of the companies from US market, I chose it for two reasons:
- US Stock Exchange represents in another quote provider, IEX Cloud service, that I use for quick checking for ticker,
- It's the market with the largest trading volume.

If you want to test other markets, you should go to `views.py` and change `companies()` function. According to **okama** 
documentation the list of available markets represented by `okama.namespaces` property.

If the user wants to add some asset to the list of favorites, first go to the `/quote` route. 
There you might find the main financial statistics that may be useful for assessing the stock.

To see the performance of one or more stock and compare them to inflation, you should go to
`/search` route (Compare link). Form provides you with multiple inputs and autocomplete function for the names of the companies,
but the actual transmitted data consists of tickers, so if you provide business names of the companies you'll get an error.

`/lists` route allows you to manage stocks that you added to the favorites. Also you can edit and delete these lists.



 
