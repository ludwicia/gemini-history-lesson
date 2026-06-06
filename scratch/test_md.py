import markdown
html = markdown.markdown("![This is a caption](images/test.jpg)")
print("HTML OUTPUT:", repr(html))
