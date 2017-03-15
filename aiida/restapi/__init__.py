# -*- coding: utf-8 -*-

the AiiDA platform. For further information please visit
http://www.aiida.net/.. All rights reserved."""

"""
In this module, AiiDA provides REST API to access different
AiiDA nodes stored in database. The REST API is implemented
using Flask RESTFul framework. The REST urls provided for
node types Computer, Node (Calculation , Data, Code), Workflows.

Examples:

Computers:
    http://localhost:5000/computers?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)?(ORDERBY)
    http://localhost:5000/computers/1

NODES / CALCULATIONS / DATAS / CODES :
(replace nodes with calculations/datas/codes)
    http://localhost:5000/nodes?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(SORT)

    OR
    http://localhost:5000/nodes/pages?(COLUMN_FILTERS)&(PER_PAGE)&(SORT)
    http://localhost:5000/nodes/pages/1?(COLUMN_FILTERS)&(PER_PAGE)&(SORT)

    http://localhost:5000/nodes/1
    http://localhost:5000/nodes/1/io
    http://localhost:5000/nodes/1/io/inputs
    http://localhost:5000/nodes/1/io/inputs?(COLUMN_FILTERS)
    http://localhost:5000/nodes/1/io/outputs
    http://localhost:5000/nodes/1/io/outputs?(COLUMN_FILTERS)
    http://localhost:5000/nodes/1/contents/attributes
    http://localhost:5000/nodes/1/contents/attributes?alist=abc
    http://localhost:5000/nodes/1/contents/attributes?nalist=c,d
    http://localhost:5000/nodes/1/contents/extras
    http://localhost:5000/nodes/1/contents/extras?elist=a,b,c
    http://localhost:5000/nodes/1/contents/extras?nelist=c,d
    ...

"""
