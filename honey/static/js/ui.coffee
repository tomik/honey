
class UIHandler
  onSynced: (game) ->
    $("#commit_toggle").hide()

  onUnsynced: (game) ->
    $("#commit_toggle").show()

@UIHandler = UIHandler

