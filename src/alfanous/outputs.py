#!/bin/python
# -*- coding: UTF-8 -*- 

##     Copyright (C) 2009-2012 Assem Chelli <assem.ch [at] gmail.com>

##     This program is free software: you can redistribute it and/or modify
##     it under the terms of the GNU Affero General Public License as published by
##     the Free Software Foundation, either version 3 of the License, or
##     (at your option) any later version.

##     This program is distributed in the hope that it will be useful,
##     but WITHOUT ANY WARRANTY; without even the implied warranty of
##     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##     GNU Affero General Public License for more details.

##     You should have received a copy of the GNU Affero General Public License
##     along with this program.  If not, see <http://www.gnu.org/licenses/>.



from alfanous.main import 	QuranicSearchEngine, FuzzyQuranicSearchEngine, TraductionSearchEngine, WordSearchEngine
from alfanous.dynamic_resources.arabicnames_dyn import ara2eng_names as Fields
from alfanous.dynamic_resources.std2uth_dyn import std2uth_words
from alfanous.TextProcessing import QArabicSymbolsFilter
import json, re

STANDARD2UTHMANI = lambda x: std2uth_words[x] if std2uth_words.has_key( x ) else x;
def FREEZE_XRANGE( d ):
	new_d = dict( d );
	for k, v in d.items():
		if v.__class__ == xrange:
			new_d[k] = str( v ) ;
	return new_d; # JSON doesnt accept serialization of xrange  


class Raw():
	""" Basic format for output, as  structures of python

	TODO Add word annotations to results
	FIXME terms are standard and Qurany corpus are uthmani   # resolve with uthmani mapping of Taha , + domains + errors
	TODO statistics of use + update_stats.js
	TODO status Messages ALL (code , message)
	"""

	DEFAULTS = {
		    "maxrange":25,
		    "results_limit":100,
		    "flags":{ "action":"error",
			      "ident":"undefined",
			      "platform":"undefined",
			      "domain":"undefined",
			      "query":"",
			      "script":"standard",
			      "vocalized": True,
			      "highlight": "css",
			      "recitation": "1",
			      "translation": None,
			      "prev_aya": False,
			      "next_aya": False,
			      "sura_info": True,
			      "word_info": True,
			      "aya_info":	True,
			      "annotation_word":False,
			      "annotation_aya":False,
			      "sortedby":"score",
			      "offset":1,
			      "range":10, # used as "perpage" in paging mode 
			      "page":1, # overridden with offset
			      "perpage":10, # overridden with range
			      "fuzzy":False,
		       }
		  }

	ERRORS = {
	     0:"success ## action=%(action)s ; query=%(query)s",
	     1:"no action is chosen or action undefined ## action=%(action)s",
	     - 1:"fail, reason unknown ## action=%(action)s ; query=%(query)s",
	    }


	DOMAINS = {
			      "action": ["search", "suggest", "show"],
			      "ident":["undefined"],
			      "platform":["undefined", "wp7", "s60", "android", "ios", "linux", "window"],
			      "domain":[],
			      "query":[],
			      "highlight": ["css", "html", "genshi", "bold", "bbcode"],
			      "script": ["standard", "uthmani"],
			      "vocalized": [True, False],
			      "recitation": [], #map(lambda x:str(x),range(30)),
			      "translation": [],
			      "prev_aya": [True, False],
			      "next_aya": [True, False],
			      "sura_info": [True, False],
			      "word_info": [True, False],
			      "aya_info":	[True, False],
			      "annotation_word":[True, False],
			      "annotation_aya":[True, False],
			      "sortedby":["total", "score", "mushaf", "tanzil", "subject"],
			      "offset":[], #xrange(6237)
			      "range":[], # xrange(DEFAULTS["maxrange"]) , # used as "perpage" in paging mode 
			      "page":[], # xrange(6237),  # overridden with offset
			      "perpage":[], # xrange( DEFAULTS["maxrange"] ) , # overridden with range
			      "fuzzy":[True, False],
		}


	IDS = {"ALFANOUS_WUI_2342R52"}


	def __init__( self, QSE_index = "../../indexes/main/", TSE_index = "../../indexes/extend/", WSE_index = "../../indexes/word/" , Recitations_list_file = "../../resources/configs/recitations.js", Translations_list_file = "../../resources/configs/translations.js", Information_file = "../../resources/configs/information.js", Hints_file = "../../resourcs/configs/hints.js", Stats_file = "../../resources/configs/stats.js" ):
		"""
		Init the search engines


		"""
		##
		self.QSE = QuranicSearchEngine( QSE_index )
		self.FQSE = FuzzyQuranicSearchEngine( QSE_index )
		self.TSE = TraductionSearchEngine( TSE_index )
		self.WSE = WordSearchEngine( WSE_index )
		##
		f = open( Recitations_list_file )
		self._recitations = json.loads( f.read() ) if f else {}

		##
		f = open( Translations_list_file )
		self._translations = json.loads( f.read() ) if f else {}
		##
		f = open( Information_file )
		self._information = json.loads( f.read() ) if f else {}
		##
		f = open( Hints_file )
		self._hints = json.loads( f.read() ) if f else {}
		##
		f = open( Stats_file )
		self._stats = json.loads( f.read() ) if f else {}
		self._init_stats()
		self.Stats_file = Stats_file

		##

		self._surates = [item for item in self.QSE.list_values( "sura" ) if item]
		self._chapters = [item for item in self.QSE.list_values( "chapter" ) if item]
		self._defaults = self.DEFAULTS
		self._flags = self.DEFAULTS["flags"].keys()
		self._fields = Fields
		self._fields_reverse = dict( ( v, k ) for k, v in Fields.iteritems() )
		self._errors = self.ERRORS
		self._domains = self.DOMAINS
		self._ids = self.IDS # dont send it to output , it's private
		self._all = {
			  "translations":self._translations,
			  "recitations": self._recitations,
			  "information":self._information,
			  "hints":self._hints,
			  "surates":self._surates,
			  "chapters":self._chapters,
			  "defaults":self._defaults,
			  "flags":self._flags,
			  "fields":self._fields,
			  "fields_reverse":self._fields_reverse,
			  "errors":self._errors,
			  "domains":FREEZE_XRANGE( self._domains ),
			  }


	def do( self, flags ):
		return self._do( flags );


	def _do( self, flags ):
		#try:
		action = flags["action"] if flags.has_key( "action" ) else self._defaults["flags"]["action"]
		ident = flags["ident"] if flags.has_key( "ident" ) else self._defaults["flags"]["ident"]
		platform = flags["platform"] if flags.has_key( "platform" ) else self._defaults["flags"]["platform"]
		domain = flags["domain"] if flags.has_key( "domain" ) else self._defaults["flags"]["domain"]
		# gather statistics
		self._process_stats( flags )

		# init the error message with Succes
		output = self._check( 0, flags )

		if action == "search":
			output.update( self._search( flags ) )
		elif action == "suggest":
			output.update( self._suggest( flags ) )
		elif action == "show":
			output.update( self._show( flags ) )
		else:
			output.update( self._check( 1, flags ) )
		#except Exception as E:
		#output=self._check(-1,flags)

		return output

	def _check( self, error_code, flags ):
		""" prepare the error messages """
		return {
		      "error":{"code":error_code, "msg":self._errors[error_code] % flags}

		     }

	def _init_stats( self ):
		### initialization of stats 
		stats = {}
		for ident in ["TOTAL"]: #self._idents.extend(["TOTAL"])
			stats[ident] = {}
			stats[ident]["total"] = 0
			stats[ident]["other"] = {}
			stats[ident]["other"]["total"] = 0
			for action in self.DOMAINS["action"]:
				stats[ident][action] = {}
				stats[ident][action]["total"] = 0
				stats[ident][action]["other"] = {}
				stats[ident][action]["other"]["total"] = 0
				for flag, domain in self.DOMAINS.items():
					stats[ident][action][flag] = {}
					stats[ident][action][flag]["total"] = 0
					stats[ident][action][flag]['other'] = 0
					for val in domain:
						stats[ident][action][flag][str( val )] = 0
		stats.update( self._stats )
		self._stats = stats


	def _process_stats( self, flags ):
		""" process flags for statistics """
		stats = self._stats
		#Incrementation 
		for ident in ["TOTAL"]: #["TOTAL",flags[ident]]
			stats[ident]["total"] += 1
			action = flags["action"]
			if action in self._domains["action"]:
				stats[ident][action]["total"] += 1
				for flag, val in flags.items():
					if flag in self._domains.keys():
						stats[ident][action][flag]["total"] += 1
						if val in self._domains[flag]:
							stats[ident][action][flag][str( val )] += 1
						else:
							stats[ident][action][flag]["other"] += 1
					else:
						stats[ident][action]["other"]["total"] += 1
			else: stats[ident]["other"]["total"] += 1
		self._stats = stats
		f = open( self.Stats_file, "w" )
		f.write( json.dumps( self._stats ) )

	def _show( self, flags ):
		"""  show metadata"""
		query = flags["query"] if flags.has_key( "query" ) else self._defaults["flags"]["query"]
		if query == "all":
			return {"show":self._all}
		elif self._all.has_key( query ):
			return {"show":{query:self._all[query]}}
		else:
			return {"show":None}

	def _suggest( self, flags ):
		""" return suggestions """
		query = flags["query"] if flags.has_key( "query" ) else self._defaults["flags"]["query"]
		try:
			output = self.QSE.suggest_all( unicode( query.replace( "\\", "" ), 'utf8' ) ).items()
		except Exception:
			output = None
		return {"suggest":output}

	def _search( self, flags ):
		"""
		return the results as json
	    """
		#flags
		query = flags["query"] if flags.has_key( "query" ) else self._defaults["flags"]["query"]
		sortedby = flags["sortedby"] if flags.has_key( "sortedby" ) else self._defaults["flags"]["sortedby"]
		range = int( flags["perpage"] ) if  flags.has_key( "perpage" )  else flags["range"] if flags.has_key( "range" ) else self._defaults["flags"]["range"]
		offset = ( int( flags["page"] ) - 1 ) * range if flags.has_key( "page" ) else flags["offset"] if flags.has_key( "offset" ) else self._defaults["flags"]["offset"] ## offset = (page-1) * perpage   --  mode paging
		highlight = flags["highlight"] if flags.has_key( "highlight" ) else self._defaults["flags"]["highlight"]
		script = flags["script"] if flags.has_key( "script" ) else self._defaults["flags"]["script"]
		vocalized = flags["vocalized"] if flags.has_key( "vocalized" ) else self._defaults["flags"]["vocalized"]
		recitation = flags["recitation"] if flags.has_key( "recitation" ) else self._defaults["flags"]["recitation"]
		translation = flags["translation"] if flags.has_key( "recitation" ) else self._defaults["flags"]["recitation"]
		prev_aya = flags["prev_aya"] if flags.has_key( "prev_aya" ) else self._defaults["flags"]["prev_aya"]
		next_aya = flags["next_aya"] if flags.has_key( "next_aya" ) else self._defaults["flags"]["next_aya"]
		sura_info = flags["sura_info"] if flags.has_key( "sura_info" ) else self._defaults["flags"]["sura_info"]
		word_info = flags["word_info"] if flags.has_key( "word_info" ) else self._defaults["flags"]["word_info"]
		aya_info = flags["aya_info"] if flags.has_key( "aya_info" ) else self._defaults["flags"]["aya_info"]
		annotation_aya = flags["annotation_aya"] if flags.has_key( "annotation_aya" ) else self._defaults["flags"]["annotation_aya"]
		annotation_word = flags["annotation_word"] if flags.has_key( "annotation_word" ) else self._defaults["flags"]["annotation_word"]
		fuzzy = flags["fuzzy"] if flags.has_key( "fuzzy" ) else self._defaults["flags"]["fuzzy"]

		#Search
		SE = self.FQSE if fuzzy else self.QSE
		res, termz = SE.search_all( unicode( query.replace( "\\", "" ), 'utf8' ) , self._defaults["results_limit"], sortedby = sortedby )
		terms = [term[1] for term in list( termz )] # TODO: I dont like this termz structure , must change it
		#pagination
		offset = 1 if offset < 1 else offset;
		range = self._defaults["maxrange"] if range > self._defaults["maxrange"] else range;
		interval_end = offset + range
		end = interval_end if interval_end < len( res ) else len( res )
		start = offset if offset < len( res ) else -1
		reslist = [] if end == 0 or start == -1 else list( res )[start:end]
		output = {}

		#if True:
		## strip vocalization when vocalized = true
		V = QArabicSymbolsFilter( shaping = False, tashkil = not vocalized, spellerrors = False, hamza = False )
		# highligh function that consider None value and non-definition
		H = lambda X:  self.QSE.highlight( X, terms, highlight ) if highlight != "none" and X else X if X else u"-----"
		# Numbers are 0 if not defined
		N = lambda X:X if X else 0
		# parse keywords lists , used for Sura names
		kword = re.compile( u"[^,،]+" )
		keywords = lambda phrase: kword.findall( phrase )
		# Tamdid devine name to avoid double Shedda on the middle Lam
		Gword_tamdid = lambda aya: aya.replace( u"لَّه", u"لَّـه" ).replace( u"لَّه", u"لَّـه" )
		##########################################
		extend_runtime = res.runtime
		# Words & Annotations

		words_output = {}
		if word_info:
			matches = 0
			docs = 0
			cpt = 1;
			annotation_word_query = u"( 0 "
			for term in termz :
				if term[0] == "aya":
					if term[2]:
						matches += term[2]
					docs += term[3]
					annotation_word_query += u" OR normalised:%s " % STANDARD2UTHMANI( term[1] )
					words_output[ cpt ] = {"word":term[1], "nb_matches":term[2], "nb_ayas":term[3]}
					cpt += 1
			annotation_word_query += u" ) "
			words_output["global"] = {"nb_words":cpt - 1, "nb_matches":matches}
		output["words"] = words_output;

		#Magic_loop to built queries of Adjacents,translations and annotations in the same time 
		if prev_aya or next_aya or translation or  annotation_aya:
			adja_query = trad_query = annotation_aya_query = u"( 0"

			for r in reslist :
				if prev_aya: adja_query += " OR gid:%s " % unicode( r["gid"] - 1 )
				if next_aya: adja_query += " OR gid:%s " % unicode( r["gid"] + 1 )
				if translation: trad_query += " OR gid:%s " % unicode( r["gid"] )
				if annotation_aya: annotation_aya_query += " OR ( aya_id:%s  AND  sura_id:%d ) " % ( unicode( r["aya_id"] ), unicode( r["sura_id"] ) )

			adja_query += " )"
			trad_query += " )" + u" AND id:%s " % unicode( translation )
			annotation_aya_query += " )"

		# Adjacents 
		if prev_aya or next_aya:
			adja_res = self.QSE.find_extended( adja_query, "gid" )
			adja_ayas = {0:{"aya_":u"----", "uth_":u"----", "sura":u"---", "aya_id":0}, 6237:{"aya_":u"----", "uth_":u"----", "sura":u"---", "aya_id":9999}}
			for adja in adja_res:
				adja_ayas[adja["gid"]] = {"aya_":adja["aya_"], "uth_":adja["uth_"], "aya_id":adja["aya_id"], "sura":adja["sura"]}
				extend_runtime += adja_res.runtime

		#translations
		if translation:
			trad_res = self.TSE.find_extended( trad_query, "gid" )
			extend_runtime += trad_res.runtime
			trad_text = {}
			for tr in trad_res:
				trad_text[tr["gid"]] = tr["text"]

		#annotations for aya words
		if annotation_aya or ( annotation_word and word_info ) :
			annotation_word_query = annotation_word_query if annotation_word and word_info else "()"
			annotation_aya_query = annotation_aya_query if annotation_aya else "()"
			annotation_query = annotation_aya_query + " 0R " + annotation_word_query
			#print annotation_query.encode("utf-8")
			annot_res = self.WSE.find_extended( annotation_query, "gid" )
			extend_runtime += annot_res.runtime
			## TODO:prepare annotations for use 


		output["runtime"] = extend_runtime
		output["interval"] = {"start":start + 1, "end":end, "total":len( res )}
		### Ayas
		cpt = start
		output["ayas"] = {}
		for r in reslist :
			cpt += 1
			output["ayas"][ cpt ] = {

		              "aya":{
		              		"id":r["aya_id"],
		              		"text":  Gword_tamdid( H( V( r["aya_"] ) ) ) if script == "standard"
		              			else  Gword_tamdid( H( r["uth_"] ) ),
		                	"traduction": trad_text[r["gid"]] if ( translation != "None" and translation ) else None,
		                	"recitation": None if not recitation else u"http://www.everyayah.com/data/" + self._recitations[recitation]["subfolder"].encode( "utf-8" ) + "/%03d%03d.mp3" % ( r["sura_id"], r["aya_id"] ),
		                	"prev_aya":{
						    "id":adja_ayas[r["gid"] - 1]["aya_id"],
						    "sura":adja_ayas[r["gid"] - 1]["sura"],
						    "text": Gword_tamdid( V( adja_ayas[r["gid"] - 1]["aya_"] ) ) if script == "standard"
		              			else Gword_tamdid( adja_ayas[r["gid"] - 1]["uth_"] ),
						    } if prev_aya else None
						    ,
		                	"next_aya":{
						    "id":adja_ayas[r["gid"] + 1]["aya_id"],
						    "sura":adja_ayas[r["gid"] + 1]["sura"],
						    "text": Gword_tamdid( V( adja_ayas[r["gid"] + 1]["aya_"] ) ) if script == "standard"
		              			else  Gword_tamdid( adja_ayas[r["gid"] + 1]["uth_"] ),
						    } if next_aya else None
						    ,

		              },

		    		"sura": {} if not sura_info
					  else  {
						  "name":H( keywords( r["sura"] )[0] ),
							  "id":r["sura_id"],
							  "type":H( r["sura_type"] ),
							  "order":r["sura_order"],
						    "stat":{
								  "ayas":r["s_a"],
								  "words":N( r["s_w"] ),
								  "godnames":N( r["s_g"] ),
								  "letters":N( r["s_l"] )
						      }

		    		},




		                "position": {} if not aya_info
		                else {
		                	"manzil":r["manzil"],
		                	"hizb":r["hizb"],
		                	"rubu":r["rub"] % 4,
		                	"page":r["page"]
		           	},

		           	"theme":{} if not aya_info
		                else	{
				    		"chapter":H( r["chapter"] ),
				    		"topic":H( r["topic"] ),
				   		 "subtopic":H( r["subtopic"] )
				 	   },

				"stat":  {} if not aya_info
		                else {
						"words":N( r["a_w"] ),
		    				"letters":N( r["a_l"] ),
		    				"godnames":N( r["a_g"] )
				}       ,

				"sajda":{} if not aya_info
		                else    {
		    				"exist":( r["sajda"] == u"نعم" ),
		    				"type":H( r["sajda_type"] ) if ( r["sajda"] == u"نعم" ) else None,
		    				"id":N( r["sajda_id"] ) if ( r["sajda"] == u"نعم" ) else None,
		    			}
		    		}

		return {"search":output}



class Json( Raw ):
	""" JSON output format """
	def do( self, flags ):
		return json.dumps( self._do( flags ) )






class Xml( Raw ):
	""" XML output format

	@deprecated: Why Xml and CompleXity?! Use jSon and Simplicity!
	"""
	def suggest( self, query ):
		""" return suggestions """
		raw_output = super( Json, self ).suggest( query )
		xml_output = "\n".join( 
			[
			'<word text="%(word)s"> %(suggestions)s </word>' % {
					"word":word,
					"suggestions": "\n".join( ['<suggestion text="%s"/>' % suggestion for suggestion in raw_output[word]] )
					}
			for word in raw_output.keys()
			]
			)
		return xml_output

	def search( self, query, sortedby = "score", offset = 1, range = 10 ):
		""" return results """
		#TODO: complete it manually or using an Python2XML dump , JSON2XML,or manually 
		schema = """
		<results runtime=%(runtime)f                > # output["runtime"
		<words nb_words=%(nb_words) global_nb_matches=%(global_nb_matches)>
			<word cpt="%cpt" text="%word" nb_matches=%(nb_matches) nb_ayas=%(nb_ayas) > *  cpt

		</words>
		<ayas total="%total" start="%start"  end="%end">
		<aya cpt=%cpt>
		<aya_info id=%id>

		<text>   </text>
		<text>


		</aya_info>




		</aya>




		</ayas>
		</results>

		"""
		return None




