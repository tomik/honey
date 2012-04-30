
#
# exposed variables from the server are:
# nodes: list of raw nodes
# commentPaths: mapping from comment paths to comment objects
# initPath: short path where to start in the game
# postUpdateURL: generated url for ajax updates posting
# postCommentURL: generated url for ajax comments posting
#

class UIHandler
  onSynced: (game) ->
    $("#commit_btn").button("reset")
    $("#commit_btn").hide()

  onUnsynced: (game) ->
    $("#commit_btn").show()

@UIHandler = UIHandler

@_bridge = new Bridge(nodes, commentPaths, initPath, new UIHandler())

sendSync = () ->
  if _bridge.isGameSynced()
    return false
  $.post(
    postUpdateURL,
    {"update_data": JSON.stringify(_bridge.getNodes())},
    (reply) ->
      if("err" of reply and reply.err)
        alert(reply["err"])
      # now the game is in sync with the server again
      _bridge.syncGame()
  )

# $ init
$ ->
  # posting comments
  $("#post_comment form input[value='Post']").click(
    (e) ->
      e.preventDefault()
      sendSync()
      $("#post_comment form input[name='short_path_json']").attr("value", JSON.stringify(_bridge.getCurrNodeShortPath()))
      # send the form via ajax
      $.post(
        postCommentURL,
        $("#post_comment form").serialize(),
        (reply) ->
          if("err" of reply and reply.err)
            alert(reply["err"])
          $("#comments").append(reply.comment_html)
          $("#post_comment_toggle").click()
        )
  )
  # toggling
  $("#edit_game_toggle").click(
    (e) ->
      e.preventDefault()
      $("#edit_game").toggle()
  )
  $("#post_comment_toggle").click(
    (e) ->
      e.preventDefault()
      $("#post_comment").toggle()
  )
  $("#commit_btn").click(
    (e) ->
      $("#commit_btn").button("loading")
      e.preventDefault()
      sendSync()
  )
  # toggle forms that have errors
  if (gameEditFormHasErrors)
    $("#edit_game_toggle").click()

