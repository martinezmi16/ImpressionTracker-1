#DeVonte' Applewhite
#02/25/15 CSE40YYY

import json,sys,datetime,time
import re
sys.path.insert(0,"PyHighcharts-master/highcharts")

from chart import Highchart
from highchart_types import OptionTypeError, Series, SeriesOptions

class mood():
	def __init__(self,interval=300):
		self.colors = {"Green": "#48DD38" ,"Red": "#FC404A", "Yellow": "#FFCF41","Blue": "#6A6AC9", "Purple": "#B133BE", "Background": "#3E3E40", "Border": "#606063", "White": "#E0E0E3", "Grid Line": "#707073", "Minor Grid Line": "#505053", "Axis Title": "#A0A0A3"}
		self.EXAMPLE_CONFIG = {
			"chart":{ 
				  "zoomType": 'x',
				  "backgroundColor": self.colors['Background'],
				  "plotBorderColor": self.colors['Border']
				},
			"title":{ 
				  "style": {
					"color":self.colors['White']
				  }
				},
			"xAxis":{ 
				  "type": 'datetime', 
				  'minRange': 1000 * 10,
				  "gridLineColor": self.colors['Grid Line'],
					"labels": {
         					"style": {
            						"color":self.colors['White']
         					}
      					},
      				  'lineColor': self.colors['Grid Line'],
      				  'minorGridLineColor': self.colors['Minor Grid Line'],
      				  'tickColor': self.colors['Grid Line'],
      				  'title': {
         				'style': {
            					'color': self.colors['Axis Title']
       					}
				  }
   				},
			"yAxis":{
      				  "gridLineColor": self.colors['Grid Line'],
      				  "labels": {
         				"style": {
            					"color":self.colors['White']
         				}
      				  },
      				  "lineColor": self.colors['Grid Line'],
      				  "minorGridLineColor": self.colors['Minor Grid Line'],
      				  "tickColor": self.colors['Grid Line'],
      				  "tickWidth": 1,
      				  "title": {
         			  	"style": {
            					'color': self.colors['Axis Title']
         			  	}
      				  }
   				},
			"legend":{
			      	  "itemStyle": {
				  	"color": self.colors['White']
			      	  },
				  "backgroundColor": self.colors['Border']
			   	}
			}
		
		self.START_TIME = datetime.datetime.now()
		self.interval = interval #interval to govern certain functions
		self.moodwords = {}
		self.moodarray = [] #net mood at each data dump
		self.countarray = [] #number of tweets per data dump
		self.moodbin = {} #holds lists of good, bad, and neutral tweet counts
		self.moodbin['good'] = []
		self.moodbin['bad'] = []
		self.moodbin['neutral'] = []
		self.moodbin['useless'] = []
		self.count = 0 #total tweets processed

		self.avg_followers_seed = []
		self.avg_followers = 0.0

		self.oldtime = None #holds the last timestamp
		self.scoredump = 0 #aggregate score between intervals
		self.goodcount = 0
		self.badcount = 0
		self.neutralcount = 0
		self.uselesscount = 0
		self.localcount = 0 #total tweets processed in an interval


	def makedate(self,datestring):
		try:
			tinfo = datestring.rstrip().split(' ')
			#tinfo contains [dayOfWeek,month,day,hour:min:sec,?,year]
			timeparts = tinfo[3].split(':')
			timestr = tinfo[5]+" "+tinfo[1]+" "+tinfo[2]+" "+tinfo[3]
			fmt = "%Y %b %d %H:%M:%S"
			t2 = datetime.datetime.strptime(timestr,fmt)
			return t2
		except KeyError:
			return None

	def load(self,posfile,negfile): #md is the mood dictionary
		f = open(posfile)
		for line in f:
			if line[0] not in ['',' ',';']: #valid data
				self.moodwords[line.rstrip().encode('utf-8')] = 1 #all positive words have a value of 1
		f.close()
		f = open(negfile)
		for line in f:
			if line[0] not in ['',' ',';']: #valid data
				self.moodwords[line.rstrip().encode('utf-8')] = -1 #all positive words have a value of 1
		f.close()
	#end def load

	def readNtweets(self,filename,N,tarray):
		count = 0;
		f = open(filename)
		for line in f:
			if count == N:
				break;
			a = json.loads(line.rstrip())
			tarray.append(a)
			count += 1
	#end def readNtweets

	def netmood(self,text):
		net = 0 #net mood starts at zero
		words = text.split() #split into an array of words

		negativeList = ["not", "none", "hardly", "rarely", "scarcely", "few", "little", "never", "neither", "nor", "nobody", "nothing", "nowhere", "isn't", "don't", "hadn't", "can't", "didn't", "won't","no"]
		tweetWords = 0
		negIndex = -1
		hasMoodWords = False

		for item in words: #go through each word
			item = re.split('[.,!?]', item)[0]

			if item in negativeList:
				negIndex = tweetWords
				tweetWords += 1
				continue


			if item in self.moodwords: #mood word detected

				hasMoodWords = True
				#print item


				if negIndex != -1:
					if tweetWords-negIndex == 1:
						net += self.moodwords[item]*(-1)
					else:
						net += self.moodwords[item]
					negIndex = -1

				else:
					net += self.moodwords[item]
			tweetWords += 1

		if hasMoodWords == False:
			net = 200


		return net
	#end def netmood

	def processTweets(self,filename,companyname,func):
		self.clear() #reset stats for next dump interval

		f = open(filename)
		for line in f:
			self.add(line) 
			
		if self.oldtime != None: #dump leftover data that didn't reach the interval
			self.moodarray.append(self.scoredump) #add net score
			self.countarray.append(self.localcount)
			self.moodbin['good'].append(self.goodcount)
			self.moodbin['bad'].append(self.badcount)
			self.moodbin['neutral'].append(self.neutralcount)

		f.close() #close file

		print "Total Tweets: %d"%(self.count)

		if func == 'line':
			outfilename = companyname.lower()+"_line.html"
			self.linegraph(companyname,outfilename,1) #adds count data
		elif func == 'pie':
			outfilename = companyname.lower()+"_pie.html"
			self.piegraph(companyname,outfilename) #single pie

	def add(self,tweet): #process a tweet
		try:
			a = json.loads(tweet.rstrip())
		except ValueError:
			return 0
		try:
			s = a['text'] #just to check if the necessary keys are found
			c = a['created_at']
		except KeyError:
			return 0

		if a['lang'] != "en":
			return 0


	

		score = self.netmood(s.lower().encode('utf-8'))


		if score > 140: #useless tweet
			self.uselesscount += 1
			score = 0
		elif score > 0: #good tweet
			self.goodcount += 1
		elif score < 0: #bad tweet
			self.badcount += 1
		else: #neutral tweet
			self.neutralcount += 1



		#calculate multiplier for more followers
		follower_multiplier = 1
		follower_count = a['user']['followers_count']
		if self.count < 30:
			self.avg_followers_seed.append(follower_count)

		elif self.count > 30:
			follower_multiplier = float(follower_count)/(self.avg_followers or 1)
			self.avg_followers = ( (self.avg_followers * self.count ) + follower_count ) / (self.count + 1)

		else:
			total_followers = 0
			for followers in self.avg_followers_seed:
				total_followers += followers
			self.avg_followers = float(total_followers)/len(self.avg_followers_seed)

		self.scoredump += score*follower_multiplier #aggregate net score






		self.localcount += 1
		self.count += 1 #bookkeeping for entire process

		if self.oldtime != None: #old time is initialized
			t = self.makedate(c) #make usable date
			if t == None: #date string malformed (shouldn't happen)
				return #cannot process the date so don't add the tweet

			diff = 0
			if t > self.oldtime: #get time difference
				diff = t - self.oldtime
			else:
				diff = self.oldtime - t
			if diff.seconds >= self.interval: #need to dump data
				self.moodarray.append(self.scoredump) #add net score
				self.countarray.append(self.localcount)
				self.moodbin['good'].append(self.goodcount)
				self.moodbin['bad'].append(self.badcount)
				self.moodbin['neutral'].append(self.neutralcount)
				self.moodbin['useless'].append(self.uselesscount)

				self.clear() #reset stats

				return 1 #let listener know data has been dumped
		else:
			self.oldtime = self.makedate(c) #make the date
		return 0 #no data has been dumped yet

	def clear(self): #reset stats for next dump
		self.oldtime = None #reset all stats for next dump
		self.scoredump = 0
		self.goodcount = 0
		self.badcount = 0
		self.neutralcount = 0
		self.localcount = 0

	def set_interval(self,value):
		self.interval = value

	def piegraph(self,companyname,filename,multi=False):
		chart = Highchart()
		chart.title(companyname)

		good = 0
		bad = 0
		neutral = 0

		if multi == False:
			good = sum(self.moodbin['good'])
			bad = sum(self.moodbin['bad'])
			neutral = sum(self.moodbin['neutral'])
	
		chart.add_data_set([["Good Tweets", int(100*good/float(self.count or 1))],
		    ["Bad Tweets", int(100*bad/float(self.count or 1))],
	["Neutral Tweets", int(100*neutral/float(self.count or 1))]],
		    series_type="pie",
		    name=companyname+" Impression Pie Chart",
		    startAngle=45)
		chart.colors([self.colors['Green'],self.colors['Red'],self.colors['Yellow']])
		chart.set_options(self.EXAMPLE_CONFIG)
		chart.show(filename)

	def linegraph(self,companyname,filename,countdata = None):
		chart = Highchart()
		chart.title(companyname)

		# Add data
		chart.add_data_set(self.moodbin['good'], series_type="column", name="Good", index=1)
		chart.add_data_set(self.moodbin['bad'], series_type="column", name="Bad", index=1)
		chart.add_data_set(self.moodbin['neutral'], series_type="column", name="Neutral", index=1)
		chart.add_data_set(self.moodarray, series_type="line", name=companyname+" raw net mood", index=1, lineWidth=4, marker={"lineColor":self.colors['White'],"radius":4,"lineWidth":2})

		# Add average mood
		if countdata != None:
			moodtotal = [self.moodbin['good'][i]+self.moodbin['bad'][i] for i in range(len(self.moodbin['good']))] #count of nonzero mood scores
			averagemood = [float(self.moodarray[i])/(moodtotal[i] or 1) for i in range(len(self.moodarray))]
			chart.add_data_set(averagemood, series_type="line", name=companyname+" average net mood", index=2)
		
		chart.colors([self.colors['Green'],self.colors['Red'],self.colors['Yellow'],self.colors['Blue'],self.colors['Purple']])

		chart.set_start_date(self.START_TIME)
		chart.set_interval(1000 * self.interval)
		chart.set_options(self.EXAMPLE_CONFIG)
		chart.show(filename)

if __name__ == "__main__":
	m = mood(120)
	m.load('text_files/positive-words.txt','text_files/negative-words.txt')
	m.processTweets('text_files/walmart.txt','Lolmart','pie')
#end main
