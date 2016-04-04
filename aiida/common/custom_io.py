

def pretty_print(str_matrix, sep = ' | '):
    """
    Prints a table for a given matrix,
    by measuring the columnwidth in advance

    :param str_matrix: A list of list of strings
    :param sep: (Optional) separator, defaults to ' | '

    print the table to stdout.
    """
    # Get maximum length of item in a column:
    colwidths = [
            max(map(len, column))
            for column
            in zip(*str_matrix)
        ]
    # now print each line:
    for row in str_matrix:
        print(
            sep.join([
                '{:{width}}'.format(rowitem, width=colwidths[colindex])
                for colindex, rowitem
                in enumerate(row)
            ])
        )
