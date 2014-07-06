"""
liege is our general case wit.ai handler

liege.web.py serves a HTTP user interface, and interacts directly with the
    Wit.ai API. You can POST to it at <host>:<port>/wit/ to submit a query.
    When the wit.ai call returns on the server, it sends a Squidwork message
    containing the result.
    The ui frontend  subscribes to wit.ai result events so it can see those,
    too.

liege.worker.py listens to wit.ai squidwork results and does things.
    The results of its operations are also broadcast as squidwork messages
"""
__author__ = 'just.1.jake@gmail.com'

if __name__ == '__main__':
    from web import main()
    main()
