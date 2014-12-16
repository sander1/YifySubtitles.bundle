from StringIO import StringIO
from zipfile import ZipFile

YIFY_SUBS_API = 'http://api.yifysubtitles.com/subs/%s'
YIFY_DL_BASE = 'http://www.yifysubtitles.com'

####################################################################################################
def Start():

	HTTP.CacheTime = CACHE_1DAY
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'

####################################################################################################
class OpenSubtitlesAgentMovies(Agent.Movies):

	name = 'YIFY Subtitles'
	languages = [Locale.Language.NoLanguage]
	primary_provider = False
	contributes_to = ['com.plexapp.agents.imdb']

	def search(self, results, media, lang):

		results.Append(MetadataSearchResult(
			id = media.primary_metadata.id,
			score = 100
		))

	def update(self, metadata, media, lang):

		for i in media.items:
			for part in i.parts:
				fetch_subtitles(part, metadata.id)

####################################################################################################
def fetch_subtitles(part, imdb_id):

	lang_list = list(set([Prefs['lang_1'], Prefs['lang_2'], Prefs['lang_3']]))

	if 'None' in lang_list:
		lang_list.remove('None')

	lang_list_iso = [get_iso_639_1(l) for l in lang_list]

	# Remove all subtitles from languages no longer set in the agent's preferences
	for l in part.subtitles:
		if l not in lang_list_iso:
			part.subtitles[l].validate_keys([])

	for l in lang_list:
		json_obj = JSON.ObjectFromURL(YIFY_SUBS_API % (imdb_id), sleep=2.0)

		if l.lower() not in json_obj['subs'][imdb_id]:
			Log('No subtitles available for language "%s"' % (l))
			return None

		rating = 0
		id = 0
		selected = None

		for st in json_obj['subs'][imdb_id][l.lower()]:

			# Skip hearing impaired subtitles
			if st['hi'] == 1:
				continue

			# Prefer higher (newer) id if rating is the same
			if st['rating'] == rating and st['id'] > id:
				rating = st['rating']
				id = st['id']
				selected = YIFY_DL_BASE + st['url']

			# Always prefer a higher rating
			elif st['rating'] > rating:
				rating = st['rating']
				id = st['id']
				selected = YIFY_DL_BASE + st['url']

			else:
				continue

			if selected:
				filename = selected.split('/')[-1]

				# Download subtitle only if it's not already present
				if filename not in part.subtitles[get_iso_639_1(l)]:

					# Cleanup other subtitles previously downloaded with this agent
					# (We want just one subtitle per language)
					part.subtitles[get_iso_639_1(l)].validate_keys([])

					zip = ZipFile(StringIO(HTTP.Request(selected).content))
					sub_data = zip.open(zip.namelist()[0]).read()

					part.subtitles[get_iso_639_1(l)][filename] = Proxy.Media(sub_data, ext='srt')

				else:
					Log('Skipping, subtitle already downloaded: %s' % (selected))

			else:
				Log('No suitable subtitle found for language "%s"' % (l))

####################################################################################################
def get_iso_639_1(language):

	languages = {
		'Albanian': 'sq',
		'Arabic': 'ar',
		'Bengali': 'bn',
		'Brazilian-Portuguese': 'pt-br',
		'Bulgarian': 'bg',
		'Bosnian': 'bs',
		'Chinese': 'zh',
		'Croatian': 'hr',
		'Czech': 'cs',
		'Danish': 'da',
		'Dutch': 'nl',
		'English': 'en',
		'Estonian': 'et',
		'Farsi-Persian': 'fa',
		'Finnish': 'fi',
		'French': 'fr',
		'German': 'de',
		'Greek': 'el',
		'Hebrew': 'he',
		'Hungarian': 'hu',
		'Indonesian': 'id',
		'Italian': 'it',
		'Japanese': 'ja',
		'Korean': 'ko',
		'Lithuanian': 'lt',
		'Macedonian': 'mk',
		'Malay': 'ms',
		'Norwegian': 'no',
		'Polish': 'pl',
		'Portuguese': 'pt',
		'Romanian': 'ro',
		'Russian': 'ru',
		'Serbian': 'sr',
		'Slovenian': 'sl',
		'Spanish': 'es',
		'Swedish': 'sv',
		'Thai': 'th',
		'Turkish': 'tr',
		'Urdu': 'ur',
		'Ukrainian': 'uk',
		'Vietnamese': 'vi'
	}

	if language in languages:
		return languages[language]
