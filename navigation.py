from lxml import etree
import requests
import sys
from StringIO import StringIO
from collections import defaultdict
from bs4 import BeautifulSoup as bs
from pprint import pformat, pprint

class ScoreStruct(object):
    def __init__(self):
        self.links = []
        self.not_links = []
        self.total_link_text = []
        self.total_non_link_text = []

        self.link_score = 0
        self.non_link_score = 0
        self.len_score = 0
        self.non_len_score = 0

        self.link_ratio = None
        self.len_ratio = None

        self.tag = None

        self.path = None

    def __repr__(self):
        
        child_links = [x.text for x in self.tag.findall('.//a')]
        return pformat(dict(
            links = self.links,
            not_links = self.not_links, 
            total_link_text = self.total_link_text, 
            total_non_link_text = self.total_non_link_text, 

            link_score = self.link_score, 
            non_link_score = self.non_link_score, 
            len_score = self.len_score, 
            non_len_score = self.non_len_score, 

            link_ratio = self.link_ratio, 
            len_ratio = self.len_ratio, 

            tag = self.path,
            child_links=child_links))

    def update_scores(self):
        """ Recalculate scores based off values"""
        
        def calc_with_depth_weight(li):
            x = 0.0
            for i in range(len(li)):
                x += li[i]/len(li)
            return x

        self.link_score = calc_with_depth_weight(self.links)
        self.non_link_score = calc_with_depth_weight(self.not_links)
        self.len_score = calc_with_depth_weight(self.total_link_text)
        self.non_len_score = calc_with_depth_weight(self.total_non_link_text)

        self.link_ratio = (self.link_score)/(self.link_score + self.non_link_score + 1.0)
        self.len_ratio = (self.len_score)/(self.len_score + self.non_len_score + 1.0)


class NavigationExtractor(object):

    structural_tags = {
            'div','table','td','tr','li','ul'
            }
    
    
    visited = set()

    def __init__(self):
        pass
    
    def _is_structural(self, tag):
        return tag.tag in self.structural_tags
    def _is_link(self, tag):
        return tag.tag == 'a' and bool(self._content(tag)),

    def _content(self, tag):
        return tag.text.strip() if tag.text else ''
    
    def join_tags(self, a, b):
        la, lb = len(a), len(b)
        minlen, maxlen = min(la, lb), max(la, lb)
        
        longer = a if la > lb else b
        
        joined = [0]*maxlen
        for ix in range(1, minlen+1):
            joined[-ix] = a[-ix] + b[-ix]
        
        for ix in range(maxlen-minlen):
            joined[ix] = longer[ix]

        return joined

    def join_ss(self, x, y):
        """ 
        Takes two ScoreStruct objects, and returns their joined values 

        """
        #TODO: remake this into a data structure with overloaded add operator

        
        ss = ScoreStruct()
        ss.links = self.join_tags(x.links, y.links)
        ss.not_links = self.join_tags(x.not_links, y.not_links)
        ss.total_link_text = self.join_tags(x.total_link_text, y.total_link_text)
        ss.total_non_link_text = self.join_tags(x.total_non_link_text,
                y.total_non_link_text)
    
        return ss
    


    def recursive_traverse(self, tag, scoremap={}, tree=None):
        """
        """
        scoremap = scoremap.copy()

        # children is a list of ScoreStruct of children
        children = []
        for child in tag:
            if child not in scoremap:
                # Perhaps we can get away with passing {} instead of scoremap
                m = self.recursive_traverse(child, scoremap, tree)
                scoremap.update(m)
                children.append(m[hash(child)])
        
        empty_struct = ScoreStruct()
        score_struct = reduce(self.join_ss, children, empty_struct)
        
        is_link = tag.tag == 'a'
        link_text_len = len(tag.text or '')

        score_struct.links.append(int(is_link))
        score_struct.not_links.append(int(not is_link))
        
        score_struct.total_link_text.append(link_text_len if is_link else 0)
        score_struct.total_non_link_text.append(link_text_len if not is_link 
                else 0)
        score_struct.tag = tag
        score_struct.path = tree.getpath(tag)
        
        score_struct.update_scores()

        scoremap[hash(tag)] = score_struct

        return scoremap
        

    def get_blocks(self, html):
        def disqualify(score):
            
            # reject links from being results
            if score.tag.tag == 'a':
                return False
            
            # TODO: pick sane defaults
            return score.link_ratio > 0.1 and score.len_ratio > 0.7

        metadata = defaultdict(dict)

        parser = etree.HTMLParser(remove_comments=True, remove_blank_text=True)
        tree = etree.parse(StringIO(html), parser)
        html = tree.getroot()
        scoremap = self.recursive_traverse(html, {}, tree)

        sorted_scores = filter(disqualify, scoremap.values())
        final_scores = set()
        
        # remove duplicate xpaths where one tag is descendant of another
        for x in sorted_scores:

            # status of whether tag should be added
            add = True
            for y in final_scores:

                # tag has a parental relationship with existing tag
                if x.path in y.path or y.path in x.path:

                    # replace old tag if new one has higher ratio
                    if x.link_ratio > y.link_ratio:
                        final_scores.remove(y)
                        final_scores.add(x)

                    # in either case, no longer add tag
                    add = False
                    break

            # no parental relationships, add tag
            if add:
                final_scores.add(x)


        return final_scores

if __name__ == '__main__':
    
    r = requests.get(sys.argv[1])
    if not r.ok:
        raise Exception(r.text)

    ne = NavigationExtractor()
    blocks = ne.get_blocks(r.text)


    pprint(blocks)
