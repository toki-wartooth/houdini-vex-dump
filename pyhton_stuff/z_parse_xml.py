from xml.dom import minidom
import os
# import path

file = "D:\\TD\\parametric_room\\__AI\\different_types.svg"
parsed = minidom.parse(file)
print parsed
print (dir (parsed))

# get all g strings
by_tagname = parsed.getElementsByTagName("g")

for i in by_tagname:
	layer_name = i.getAttribute("id") # взяли значение за ляшку
	for n in i.childNodes:
		# i.createAttribute("layername")
		i.setAttribute("layername", layer_name)




## [<DOM Text node "u'\n\t'">, <DOM Element: line at 0x29b4af8>, <DOM Text node "u'\n\t'">, <DOM Element: line at 0x29b4e90>, <DOM Text node "u'\n'">]