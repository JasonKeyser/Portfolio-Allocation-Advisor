import pandas as pd
from datetime import timedelta, date
import random
import yfinance as yf
from matplotlib import pyplot as plt


def rdata(t, yrs):
    # this grabs the stock price data from the yahoo finance api
    stock2 = yf.Ticker(str(t.upper()))

    # formats the date range to grab historical data from yahoofinance api
    lastdate = date.today()
    firstdate = lastdate - timedelta(days=364.25*yrs)

    historical = stock2.history(start=firstdate, end=lastdate, interval='1d')

    if historical.empty:
        raise Exception(str(t.upper() + ' is not a valid ticker. Check yahoo finance and run again.'))

    stock1name = str(t.upper())

    # renames closing price column for clarity and drops other columns
    historical = historical.rename(columns = {'Close': stock1name})

    historical = historical.drop(columns= ['Open', 'High', 'Low', 'Stock Splits', 'Volume','Dividends'])

    # finds the stock price at business quarter ends for all years specified in yrs
    cdf = historical[stock1name].resample('BQ').asfreq(fill_value=-1).tail(yrs*4)

    # occasionally the stock market is closed on business quarter ends. (fill_value = -1 temporarily, see above) On these days the previous closing price is used via following loop
    ic = 0
    for price in cdf:
        if ic < len(cdf) - 1:
            if price == -1:
                nominutes = str(cdf.index[ic] - timedelta(days=1))
                cdf.iloc[ic] = historical.loc[nominutes[:-9], stock1name]
                ic += 1
            else:
                ic += 1
    print('\n' + stock1name + " Business Quarter End Prices")
    print(cdf)

    # this takes the price data, makes a new data frame with returns data
    i = 0
    for _ in cdf:
        # closing prices are adjusted for stock splits and dividend returns
        ret = (cdf.iloc[min(i + 1, cdf.count() - 1)] / cdf.iloc[i]) - 1
        if i < 1:
            d = {'Date': cdf.index[i + 1], stock1name: ret}
            bdf = pd.DataFrame(data=d, index= [0])
        elif i < cdf.count() - 2:
            f = {'Date': cdf.index[i + 1], stock1name: ret}
            bdf = bdf.append(f, ignore_index= True)
        i += 1
    return bdf


def effic_front(co, pa, me, sd, r):
    # these loops generate random weights on each asset (portfolio weight always sums to one)
    weights = {}
    for stock in stocks:
        weights[stock] = random.random()

    weight_sum = sum(weights.values())
    for stock in stocks:
        weights[stock] = weights[stock]/weight_sum

    er = 0
    sdterm1 = 0
    sdterm2 = 0

    # this calculates portfolio expected return
    for stock in stocks:
        er += weights[stock]*me[stock.upper()]

    # this loop calculates one term in the portfolio variance equation
    for stock in stocks:
        sdterm1 += (weights[stock]**2)*(sd[stock.upper()]**2)

    # this loop caculates the second term of portfolio variances
    for copair in pa:
        sdterm2 += (2*weights[copair[0].lower()]*weights[copair[1].lower()]*co.loc[copair[0], copair[1]])

    # portfolio variance
    portvar = sdterm1 + sdterm2

    # portfolio standard deviation
    port_sd = portvar**.5

    # sharp ratio
    sharp = (er-r)/port_sd
    return weights, sharp, port_sd, er


def generate_portfolios(stocks):
    c = 0
    ports = []
    ns = min((10 ** len(stocks)) + 10000, 50000)
    while c < ns:
        test = effic_front(covs, pairs, means, sds, rfr)
        ports.append(test)
        c += 1
    return ports


def take_input():
    welcome = input(
        '\nWelcome to the Portfolio Allocation Advisor\npress L to learn more about this program, or S to start    ')

    if welcome.lower() == 'l':
        print(
            "\nWHO SHOULD USE THIS PROGRAM\nThis program is designed to help small investors capture diversification synergies "
            "cheaply without investing \nin ETF's, Mutual Fund's, or spreading capital too thinly across a plethora of stocks.\n\nHOW DOES THE PROGRAM WORK\nThis program uses Markowitz Porftolio Theory to calculate the 'Optimal Portfolio Allocation'. The optimal portfolio is the one which maximizes diversification \n"
            "benefits, resulting in the highest returns per unit of risk (as measured in standard deviation of returns). This program pulls price data (adjusted for dividends) \nfrom yahoo finance to make calculations of average returns,"
            "standard deviations of returns, and correlation of returns between assets in your portfolio. The default \ntime horizon is 5 years (secret tip: time horizon can be changed "
            "by entering 'd' to the welcome prompt). Returns are calculated "
            "on business quarter intervals. \n13 month maturity US Treasury Bond yields are used to approximate the risk free rate of interest.\n\nHOW TO USE THIS PROGRAM\n"
            "Enter the number of assets which are in your portfolio. Note, this program works best for portfolios with 3-5 assets, and results become less meaningful as \n"
            "number of assets increase. Enter the ticker symbols of your assets as listed on the Yahoo Finance Website. For stocks listed on the NYSE and Nasdaq, \n"
            "tickers will be the same as their listed ticker. For assets such as cryptocurrencies, precious metals, Futures Contracts etc. Yahoo Finance may have a unique \n"
            "symbol. Check with the website.\n\nHOW TO INTERPERET RESULTS\nThe advised allocation should not be taken as gospel. It is information which can supplement your current investment \n"
            "strategy, giving you understanding of where efficiencies can be gained in diversification. The advised allocation is more meaningful for value investing \n"
            "strategies. In the short-term (less than 6 months) assets are more likely to deviate from historical trends. In the long-term, rebalancing of capital \n"
            "is necessary to maintain the advised proportions (also with new data the advised proportions could change).")
        dyears = 5
    elif welcome.lower() == 'd':
        dyears = int(input('\nHow many years of price data would you like to include in the calculations? '))
    else:
        dyears = 5

    amountofstocks = int(input('\nType number of assets in portfolio and hit enter '))

    return dyears, amountofstocks


if __name__ == "__main__":
    stocks = []

    dyears, amountofstocks = take_input()

    for _ in range(amountofstocks):
        stock = input('Type asset ticker name ')
        stocks.append(stock.lower())

    for i, stock in enumerate(stocks):
        if i == 0:
            masterframe = rdata(stock, dyears)
        else:
            asset2 = rdata(stock, dyears)
            masterframe = masterframe.merge(asset2, on='Date')
            masterframe.set_index('Date', inplace=True)

    print('\nAsset Returns')
    print(masterframe)

    # returns a matrix with sample covariances
    covs = masterframe.cov()
    print('\nCovariance Matrix of Asset returns')
    print(covs)

    corrs = masterframe.corr()
    print('\nCorrelation Matrix of Asset returns')
    print(corrs)

    # this loop creates a list of pairs of stocks for looping over the covariance matrix
    pairs = []
    for numb in stocks:
        for nu in stocks:
            if numb > nu:
                pair = [numb.upper(), nu.upper()]
                pairs.append(pair)

    means = {}
    sds = {}
    for tick in masterframe:
        means[tick] = masterframe[tick].mean()
        sds[tick] = masterframe[tick].std()

    # risk free rate stand in
    enddate = date.today()
    begindate = enddate - timedelta(days=364.25*dyears)

    # risk free rate is the average of 13 month US Treasury bill rates for the same period length as stock data
    treasury = yf.Ticker('^IRX')

    historical = treasury.history(start=begindate, end=enddate, interval='3mo')

    rfr = (historical['Close'].mean())/100/4
    print('\nrisk free rate of interest is ', rfr)

    # this loop generates thousands of different portfolios with random weights (portfolio weights always add to 1)
    port = generate_portfolios(stocks)

    # this makes a data frame out of the many generated portfolios
    ports = pd.DataFrame(port, columns=['Weights', 'Sharpe', 'S_Deviation', 'Expected Return'])

    # this finds the portfolio of all randomly generated mixes with the highest sharpe ratio
    filt = (ports['Sharpe'] == ports['Sharpe'].max())
    gdf = ports.loc[filt, "Weights"]
    max_shrp = ports.loc[filt]
    shrpw = gdf.iloc[0]
    filt2 = (ports['S_Deviation'] == ports['S_Deviation'].min())
    min_sd = ports.loc[filt2]

    print("                                               The optimal (tangent) portfolio allocation is: ")
    for stock in stocks:
        print("                                                                " + stock, round(shrpw[stock]*100, 2), "%")

    # defines slope equation for capital market line
    m = (max_shrp.iloc[0, 3] - rfr)/(max_shrp.iloc[0, 2] - 0)
    x = max_shrp.iloc[0, 2] * 1.5
    y = m*x + rfr
    cmlx = [0, x]
    cmly = [rfr, y]

    # defines everything to be plotted
    plt.style.use('ggplot')

    plt.scatter(ports['S_Deviation'], ports['Expected Return'], color = 'b', zorder=0, s=15)

    plt.scatter(max_shrp['S_Deviation'], max_shrp['Expected Return'],color='gold', marker = "*",s = 60, zorder=2, label = 'Tangency Portfolio')

    plt.scatter(min_sd['S_Deviation'], min_sd['Expected Return'],color = 'r', s = 60,zorder=2, marker = "*",label = 'Minimum Variance Portfolio')

    plt.scatter(0, rfr, color = 'g', s = 60, zorder=2, marker='*', label = 'Risk Free Rate')

    plt.plot(cmlx, cmly, linestyle = '-.', linewidth = 1, label= 'Capital Market Line')


    plt.ylabel('Expected Quarterly Return')
    plt.xlabel('Standard Deviation')
    plt.title('Efficient Frontier')

    plt.legend()

    plt.show()
