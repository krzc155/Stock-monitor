from kivy.uix import *
from kivy.uix.anchorlayout import *
from kivy.uix.relativelayout import *
from kivy.uix.textinput import TextInput
from kivy.graphics import *
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.datatables import MDDataTable
from kivy.properties import StringProperty
from kivy.uix.tabbedpanel import TabbedPanelHeader
from kivy.uix.widget import *
from kivy.lang import Builder
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
import matplotlib.dates as mdates

from kivy.config import Config
Config.set('graphics', 'width', '1500')
Config.set('graphics', 'height', '900')
Config.write()
#Window.size = (1500, 800)


 
def __init__(self, **kwargs):
        pass


class MainApp(MDApp): 
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        return Builder.load_file('design.kv')  



    def on_start(self):
        self.instance = self.root.add_widget(Lay()) 


class TabContent(RelativeLayout):
    def fillTab(self, ticker, tabheader, speriod):
        stockData = yf.Ticker(ticker)
        self.tabheader = tabheader
        self.ticker = ticker
        self.speriod = speriod
        self.history = stockData.history(period = speriod)
        if self.speriod == "max":
            self.altHistory = stockData.history(period ="max")
        else:
            self.altHistory = stockData.history(period ="10y")
        tabheader.content = self
        self.assign(stockData)
        self.graphs(stockData)

    def assign(self, data):
        self.ids.symbol.text = self.ticker
        self.ids.comname.text = data.info['shortName']
        self.ids.pe.text = str(data.info['trailingPE'])
        self.ids.fpe.text = str(data.info['forwardPE'])
        self.ids.eps.text = str(data.info['trailingEps'])
        self.ids.ndividend.text = f"{data.info['trailingAnnualDividendRate']}({data.info['fiveYearAvgDividendYield']}%)"
        self.ids.close.text = str(round(self.history['Close'].iloc[-1], 2))
        self.ids.closerange.text = f"{round(self.history['Close'].iloc[0], 2)} - {round(self.history['Close'].iloc[-1], 2)}"
        self.ids.marketcap.text = str(data.info['marketCap'])
        self.ids.volume.text = str(data.info['regularMarketVolume'])
        
        
    def getDividend(self):
        divHistory = self.altHistory[self.altHistory['Dividends']>0]
        divHistory['Dividend Yield'] = divHistory['Dividends']/divHistory['Close']*100
        DividendYield = divHistory[['Dividend Yield', 'Dividends']].groupby(divHistory.index.year).sum()
        return DividendYield

    def plotGraph(self, x, y, title, element, yscale):
        plt.style.use('dark_background')
        fig = plt.figure()
        plt.plot(x, y, c="green", linestyle='solid')
        plt.margins(x=0, y=0)
        plt.title(title)
        plt.yscale(yscale)
        
        
        
        element.add_widget(FigureCanvasKivyAgg(fig))
        

    def graphs(self, sData):
        dividends = self.getDividend()
        change = self.altHistory.groupby(self.altHistory.index.year)[['Close']]
        change =change.nth([0]).pct_change()*100
        change.iloc[0] = 0
        print(self.history)
        if self.speriod == "max" or "10y" or "5y":
            ghistory = self.history.groupby(pd.Grouper(freq="M"))[['Close']]
        else:
            ghistory = self.history.groupby(pd.Grouper(freq="D"))[['Close']]
        
        ghistory= ghistory.nth([-1])
        
        self.plotGraph(ghistory.index, ghistory, f"Price change over time", self.ids.box, "linear")
        self.plotGraph(change.index, change, f"Yearly change of price in % ", self.ids.box2, "linear")
        plt.axhline(y=0.5, color='r', linestyle='-')
        self.plotGraph(dividends['Dividends'].index, dividends['Dividends'], f"Dividends absolute", self.ids.box3, "linear")
        self.plotGraph(dividends['Dividend Yield'].index, dividends['Dividend Yield'], f"Dividend rate yearly", self.ids.box4, "linear")

    
        

class Lay(RelativeLayout):
    tab1Checked = []
    tab2Checked = []
    tabsData = {}
    try:
        sFileData = pd.read_csv("Saved Stonks.csv")

    except:
       sFileData = pd.DataFrame(columns =['Ticker', 'Stock Name']) 
       sFileData.to_csv('Saved Stonks.csv', index=False)
    savedFile = "Saved Stonks.csv"
    stockFile = "DJIA.csv"
    periods = {
        0.0: "error?",
        1: "5d",
        2: "1mo",
        3: "3mo",
        4: "6mo",
        5: "ytd",
        6: "1y",
        7: "2y",
        8: "5y",
        9: "10y",
        10: "max"
        }
    
    def addTab(self, name, period): #Creating tab object
        tabheader = TabbedPanelHeader(text=name)
        
        self.ids.tabz.add_widget(tabheader)
        self.tabsData[name] = TabContent()
        self.tabsData[name].fillTab(name, tabheader, period)


    def add_table(self): 
        dtable = MDDataTable(
            pos_hint={'top': 0.88, 'center_x': 0.5},
            size_hint=(0.97, 0.8),
            use_pagination=True,
            check = True,
            pagination_menu_height = '240dp',
            rows_num = 15,
            column_data=[
                ("Ticker", dp(35),self.sort_col_1),
                ("Stock Name", dp(45),self.sort_col_2),
                ("Close", dp(30),self.sort_col_3),
                ("High", dp(30),self.sort_col_4),
                ("Low", dp(30),self.sort_col_5),
                ("Change", dp(30),self.sort_col_6),
                ("Volume", dp(30),self.sort_col_7), ],
            
            sorted_on="Ticker",
            sorted_order="DSC",
            elevation=0,
            )
        return dtable
        

    def coo(self): #adding tables to program and setting binds on them
        self.tab1 = self.add_table()
        self.tab2 = self.add_table()

        self.ids.research.add_widget(self.tab1)
        self.ids.saved.add_widget(self.tab2)
        self.tab1.bind(on_row_press=self.on_row_check)
        self.tab1.bind(on_check_press=self.on_check_press1)
        self.tab1.bind(on_touch_down = self.huh)
        self.tab2.bind(on_row_press=self.on_row_check2)
        self.tab2.bind(on_check_press=self.on_check_press2)
        self.tab2.bind(on_touch_down = self.huh)
        

    def add_row1(self, instance, stonkFile, stockPeriod):
        try:
            for r in instance.row_data[0:]:
                instance.remove_row(r)
            ticks= ""
            company = pd.read_csv(stonkFile)
            tickers = company.iloc[:, :1]
            for i, index in enumerate(tickers.values):
                ticks += company.iloc[i][0] + " "

            data = yf.download(tickers =ticks ,
                    period = stockPeriod,
                    interval = "1d",
                    group_by = 'ticker',
                    prepost = False,
                    threads = True
                )
            tup=[]
            self.atup=[]
            i= 0
            for i, index in enumerate(tickers.values):
                change = round((data[index[0]].iloc[-1, 3] / data[index[0]].iloc[0, 3])*100 -100, 1)
                tup = [company.iloc[i][0], company.iloc[i][1], round(data[index[0]].iloc[-1, 3], 3), round(data[index[0]].iloc[-1, 1], 2), str(round(data[index[0]].iloc[-1, 2], 3)), change,(data[index[0]].iloc[-1, 5])]
                instance.add_row(tup)
                self.atup += tup
            print(self.atup)
        except Exception as err:
            print(err)

    

    def addToSaved(self, instance):
        self.checkDf = pd.DataFrame(self.tab1Checked, columns =['Ticker', 'Stock Name'])
        print(self.checkDf.iloc[:, :2])
        self.sFileData = self.sFileData.append(self.checkDf.iloc[:, :2], ignore_index=True)
        self.sFileData = self.sFileData.drop_duplicates()
        self.sFileData.to_csv('Saved Stonks.csv', index=False)

    def removeFromSaved(self, instance):
        self.tab2Checked = pd.DataFrame(self.tab2Checked, columns =['Ticker', 'Stock Name'])
        self.sFileData = self.sFileData[self.sFileData.Ticker.isin(self.tab2Checked.iloc[:, 0]) == False]
        print(self.sFileData)
        self.sFileData.to_csv('Saved Stonks.csv', index=False)
        self.tab2Checked = []
        self.add_row1(instance, self.savedFile, self.periods[self.ids.sliderr1.value])

    def add_ticker(self):
        try:
            if self.sFileData.Ticker.isin([self.ids.tickerinput.text]).any()== False:
                self.searchedTicker = yf.Ticker(self.ids.tickerinput.text)
                self.sFileData = self.sFileData.append({'Ticker': self.ids.tickerinput.text, 'Stock Name': self.searchedTicker.info['longName']}, ignore_index=True)
                self.sFileData.to_csv('Saved Stonks.csv', index=False)
                self.add_row1(self.tab2, self.savedFile, self.periods[self.ids.sliderr1.value])
            else:
                self.showDialog("This stock is already saved")

        except:
            self.showDialog("No such ticker found")

    
    def on_check_press1(self, instance_table, instance_row):
            if instance_row[0:2] in self.tab1Checked:
                print(instance_row)
                self.tab1Checked.remove(instance_row[0:2])
            else:
                self.tab1Checked += [instance_row[:2]]
                print("ok")
    
    def on_check_press2(self, instance_table, instance_row):
            if instance_row[0:2] in self.tab2Checked:
                print(instance_row)
                self.tab2Checked.remove(instance_row[0:2])
            else:
                self.tab2Checked += [instance_row[:2]]
                print("ok")

    def huh(self, touch, click):
            self.click = click

    def on_row_check(self, instance_table, instance_row):
        if self.click.is_double_tap:
            rpp = instance_row.parent.table_data.rows_num
            print(rpp)
            pageCells = rpp * 7
            drow = instance_table.row_data[int((instance_row.index + instance_row.parent.table_data._rows_number*pageCells)/7)]
            self.addTab(drow[0], self.ids.slabel.text)

    def on_row_check2(self, instance_table, instance_row):
        if self.click.is_double_tap:
            rpp = instance_row.parent.table_data.rows_num
            print(rpp)
            pageCells = rpp * 7
            drow = instance_table.row_data[int((instance_row.index + instance_row.parent.table_data._rows_number*pageCells)/7)]
            self.addTab(drow[0], self.ids.slabel1.text)

        else:
            pass
    
    def showDialog(self, message):
        self.dialog = MDDialog(
                text=message,
                buttons=[
                    MDFlatButton(
                        text="DISCARD",
                        theme_text_color="Custom",
                        #text_color=self.theme_cls.primary_color,
                        on_press = self.dialog_close
                    ),
                ],
            )
        self.dialog.open()

    def dialog_close(self, obj):
       self.dialog.dismiss()

    def sort_col_1(self, data):
        return zip(*sorted(enumerate(data), key=lambda l: l[1][0]))
    def sort_col_2(self, data):
        return zip(*sorted(enumerate(data), key=lambda l: l[1][1]))
    def sort_col_3(self, data):
        return zip(*sorted(enumerate(data), key=lambda l: l[1][2]))
    def sort_col_4(self, data):
        return zip(*sorted(enumerate(data), key=lambda l: l[1][3]))
    def sort_col_5(self, data):
        return zip(*sorted(enumerate(data), key=lambda l: l[1][4]))
    def sort_col_6(self, data):
        return zip(*sorted(enumerate(data), key=lambda l: l[1][5]))
    def sort_col_7(self, data):
        return zip(*sorted(enumerate(data), key=lambda l: l[1][6]))



if __name__ == '__main__':
    MainApp().run()