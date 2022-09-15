from markdown.extensions.footnotes import FootnoteExtension
import xml.etree.ElementTree as etree


class MyFootnoteExtension(FootnoteExtension):
    def makeFootnotesDiv(self, root):
        # get the normal footnotes div
        div = super().makeFootnotesDiv(root)

        # remove <hr>
        hr = div.find("hr")
        div.remove(hr)

        return div
