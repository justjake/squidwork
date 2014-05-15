"""
squidwork.web.monitor - shows the latest {{ count }} squidwork messages,
and the latest of each type of message

runtime dependencies: the Mithril javascript library,
  http://lhorie.github.io/mithril/getting-started.html

TODO: re-write in mithril
"""

# explicit imports
squidwork = window.squidwork
m = window.Mithril

# app settings passed form the backend
LIMIT = parseInt('{{ count }}', 10)

###############################################################################
#                                  VIEWS                                      #
###############################################################################

AppView = (ctrl) ->
  window.controller = ctrl
  m 'html', [
    m('head', [
      m('title', 'squidwork.web.monitor'),
      m('link[rel=stylesheet][href=/style.css]')
    ]),
    m 'body', [
      SideView('Latest Events', ctrl.latest()),
      SideView('By Origin', ctrl.by_origin())
    ]
  ]

SideView = (heading, msgs) ->
  m 'section.side', [
    m('h2', heading),
    m 'ol.message-list', msgs.map (msg) ->
      m 'li.message', {class: msg.origin.toString()}, [
        m('.info', [
          m('span.origin', msg.origin.toString()),
          m('span.time', msg.time.toString())
        ]),
        m '.data', render_json(msg.content)
      ]
  ]

render_json = (data) ->
  # adapted from http://stackoverflow.com/questions/4810841/how-can-i-pretty-print-json-using-javascript
  # wraps JSON data in span elements so that syntax highlighting may be
  # applied. Should be placed in a `whitespace: pre` context
  if typeof(data) isnt 'string'
    data = JSON.stringify(data, undefined, 2)

  # these regexes are ORed together to form the JSON tokenizer
  unicode =     /"(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?/
  keyword =     /\b(true|false|null)\b/
  whitespace =  /\s+/
  punctuation = /[,.}{\[\]]/
  number =      /-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/

  # combine by | or-ing
  syntax = '(' + [unicode, keyword, whitespace,
            punctuation, number].map((r) -> r.source).join('|') + ')'
  parser = new RegExp(syntax, 'g')

  nodes = data.match(parser) ? []
  select_class = (node) ->
    if punctuation.test(node)
      return 'punctuation'
    if /^\s+$/.test(node)
      return 'whitespace'
    if /^"/.test(node)
      if /:$/.test(node)
        return 'key'
      return 'string'

    if /true|false/.test(node)
      return 'boolean'

     if /null/.test(node)
       return 'null'
     return 'number'
  return nodes.map (node) ->
    cls = select_class(node)
    return m('span', {class: cls}, node)


###############################################################################
#                                  MODELS                                     #
###############################################################################

class MessageCache
  """
  keep a cache of the @max_count last messages, as well as a map of the latest
  message from each origin
  """
  constructor: (@max_count, latest=[], by_origin={}) ->
    @cache = []
    @callbacks = []
    @by_origin = {}
    @insert(latest...)
    # explicity set by_origin after add so we have the correct
    # initial state
    @by_origin = by_origin

  insert: (messages...) ->
    for msg in messages
      @by_origin[msg.origin] = msg

    @cache = @cache.concat(messages)[-@max_count..]


###############################################################################
#                                CONTROLLERS                                  #
###############################################################################
class MainController
  """
  application controller. created on page load.
  """
  constructor: () ->
    # vivify JSON into Message objects
    latest = window.initial_state.latest.map (m) ->
      new squidwork.Message(m.content, m.origin, m.time)

    my_types = {}
    types = window.initial_state.types
    for origin of types
      my_types[origin] = new squidwork.Message(
        types[origin].content, origin, types[origin].time)

    @cache = new MessageCache(LIMIT, latest, my_types)

    # collect all unique endpoints from the services list
    uris = {}
    for svc in config.Services
      for uri in svc.uris
        uris[uri] = true

    # subscribe to all ('' matches everything)
    for uri of uris
      squidwork.subscribe(uri, '', @recieve_message)


  recieve_message: (msg) =>
    # will be used as a squidwork subscription callback
    @cache.insert(msg)
    m.redraw()

  latest: () -> @cache.cache.sort((a, b) -> b.time - a.time)
  by_origin: () ->
    """
    gets the unique items, sorts them by time, limits them to 15,
    and then sorts them by name
    """
    msgs = []
    for origin of @cache.by_origin
      msgs.push(@cache.by_origin[origin])
    msgs = msgs.sort((a, b) -> b.time - a.time)
    # get the latest items
    msgs = msgs[-LIMIT..]
    # re-sort by origin
    return msgs.sort((a, b) -> (a.origin.toString() > b.origin.toString()))

###############################################################################
#                               ENTRY POINT                                   #
###############################################################################

app = window.app = {}
app.MessageCache = MessageCache
app.MainController = MainController
app.AppView = AppView

Mithril.module(document, {view: AppView, controller: MainController})
