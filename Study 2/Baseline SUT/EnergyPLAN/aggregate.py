# -*- coding: utf-8 -*-
"""
Created on Wed Nov 15 16:25:42 2023

@author: loren
"""

import mario
path = 'flows'
world = mario.parse_from_txt(path,'SUT',path)

# world.get_aggregation_excel('aggr.xlsx')
world.aggregate('aggr.xlsx',ignore_nan=True)
world.to_txt(path,path)
