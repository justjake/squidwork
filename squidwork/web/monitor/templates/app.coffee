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
    m 'body', [
      SideView('Latest Events', ctrl.latest()),
      SideView('By Origin', ctrl.by_origin())
    ]
  ]

SideView = (heading, msgs) ->
  m 'section.side', [
    m('h2', heading),
    m 'ul.message-list', msgs.map (msg) ->
      m '.message', {class: msg.origin.toString()}, [
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
  parser = /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g
  nodes = data.match(parser) ? []
  select_class = (node) ->
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
    @cache = new MessageCache(
      LIMIT,
      window.initial_state.latest,
      window.initial_state.types)
      # todo: subscribe to all services

  recieve_message: (msg) =>
    # will be used as a squidwork subscription callback
    @cache.insert(msg)
    m.redraw()

  latest: () -> @cache.cache
  by_origin: () ->
    """
    gets the unique items, sorts them by time, limits them to 15,
    and then sorts them by name

    TODO: implement
    """
    return []

###############################################################################
#                               ENTRY POINT                                   #
###############################################################################

app = window.app = {}
app.MessageCache = MessageCache
app.MainController = MainController
app.AppView = AppView

Mithril.module(document, {view: AppView, controller: MainController})
