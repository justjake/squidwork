"""
squidwork.web.monitor - shows the latest {{ count }} squidwork messages,
and the latest of each type of message

runtime dependencies: the Mithril javascript library,
  http://lhorie.github.io/mithril/getting-started.html

TODO: re-write in mithril
"""

LIMIT = {{ count }}

# both view classes are singletons -- they could just be nested functions
# i'm using classes to allow for inheritance or something
class MessageView
  renderMetadata: (msg) ->
    """
    <span class="origin">#{msg.origin.toString()}</span>
    <span class="time">#{msg.time.toString()}</span>
    """

  renderData: (msg) ->
    # adapted from http://stackoverflow.com/questions/4810841/how-can-i-pretty-print-json-using-javascript
    json = JSON.stringify(msg.content, undefined, 2)
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    parser = /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g
    return json.replace(parser, (match) ->
      cls = 'number'
      if /^"/.test(match)
        if /:$/.test(match)
          cls = 'key'
        else
          cls = 'string'
      else if /true|false/.test(match)
        cls = 'boolean'
      else if /null/.test(match)
        cls = 'null'
      return """<span class="#{cls}">#{match}</span>"""

  render: (msg) ->
    # look ma, straight up html views.
    """
    <div class="message #{msg.origin.path}">
      <div class="info">
        #{@renderMetadata(msg)}
      </div>
      <div class="data">
        #{@renderData(msg)}
      </div>
    </div>
    """

class MessageListView
  constructor: (@msgview) ->
  render: (msgs) ->
    each = ["<li>#{@msgview.render(msg)}</li>\n" for msg in msgs].join("\n")
    """
    <ul class="messages">
      #{each}
    </ul>
    """

list_view = new MessageListView(new MessageView())
