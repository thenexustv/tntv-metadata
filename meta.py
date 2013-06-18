
from mutagen.mp3 import MP3
from mutagen.id3 import *
from mutagen.id3 import TIT2, TALB, TCOM, TCON, TDRC, TPE1, TPE2, TRCK, APIC, TPUB
from datetime import date
import yaml
import argparse
import re

quiet_output = False

def output_hook(string):
	if not quiet_output:
		print string

def join_and(li):
	if len(li) <= 2:
		return ' and '.join(li)
	else:
		return ', '.join(li[:-1]) + (' and ' + li[-1])

def parse_file_name(name):
	filename = name.split('/')
	parts = filename[-1].split('.')
	string = parts[0]
	number = re.sub('[^0-9]', '', string)
	short = re.sub('[0-9]', '', string)
	return {'name': short, 'number': number}

def find_show(name, shows):
	for key, show in shows.iteritems():
		if name == show['short']:
			return key
	return 'xx'

def get_arguments():
	parser = argparse.ArgumentParser(description='Sets episode metadata')
	parser.add_argument('file', type=file, help="The episode file to set metadata on")
	parser.add_argument('title', help="The title of the episode e.g. Show #xx: {title}")
	parser.add_argument('-m', '--members', nargs='*', help="Additional members to include in the episode")
	parser.add_argument('-s', '--show', help="Override the auto-determined show name with provided short name (e.g 'atn')")
	parser.add_argument('-n', '--number', type=int, help="The episode number")
	parser.add_argument('--quiet', dest='quiet', action='store_true', help="Display no output")

	return parser.parse_args()

def get_title(data, show):
	title = show['formal'] + ' #' + str(data['number']) + ": " + data['title']
	return title

def set_metadata(data, show):
	audio = ID3(data['filename'])
	members = show['members'] + data['members']

	title = get_title(data, show)
	album = show['formal']
	composer = data['composer']
	genre = 'Podcast'
	year = str(date.today().year)
	track_artist = join_and(members)
	album_artist = data['artist']
	track_number = str(data['number'])
	album_art = data["art_path"] + show["album_art"]

	tit2 = TIT2(encoding=3, text=title)
	talb = TALB(encoding=3, text=album)
	tcom = TCOM(encoding=3, text=composer)
	tcon = TCON(encoding=3, text=genre)
	tdrc = TDRC(encoding=3, text=year)
	tpe1 = TPE1(encoding=3, text=track_artist)
	tpe2 = TPE2(encoding=3, text=album_artist)
	trck = TRCK(encoding=3, text=track_number)
	tpub = TPUB(encoding=3, text=album_artist)

	image = open(album_art, 'rb').read()
	apic = APIC(3, 'image/jpg', 3, 'Front cover', image)

	output_hook("Writing tags...")

	elements = [tit2, talb, tcom, tcon, tdrc, tpe1, tpe2, tpub, trck, apic]
	audio.delete()
	for element in elements:
		audio.add(element)

	output_hook("Saving tags...")
	audio.save()

def get_data(file):
	f = open(file)
	data = yaml.load(f)
	return data;

def main():
	args = get_arguments()

	if args.quiet is not None:
		quiet_output = True

	output_hook("Reading configuration...")

	data = get_data('config.yaml')
	data['filename'] = args.file.name;
	fn = parse_file_name(data['filename'])
	data['name'] = fn['name']
	data['number'] = fn['number']
	data['title'] = args.title
	data['members'] = args.members

	# massage the members array; pass in an empty list otherwise
	if args.members is None or len(args.members) <= 0:
		data['members'] = []

	# massage the show_key variable; override autodetermine by file name
	if args.show is not None and args.show in data['shows']:
		data['name'] = args.show

	# massage episode number; override is possible
	if args.number is not None and args.number > 0:
		data['number'] = args.number

	data['show_key'] = find_show(data['name'], data['shows'])
	show = data['shows'][data['name']]

	output_hook("Setting metadata for " + get_title(data, show) + "...")

	set_metadata(data, show)

	output_hook("\tID3 metadata saved for " + data['filename'] + ": " + get_title(data, show) + ".")

# ---
main()