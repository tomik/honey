
import db

def migrate_1():
    """
    Players were added. Make sure that every game has a player.
    """
    # update the structure
    db.db_games.update({"player1_id": {"$exists": False}}, {"$set": {"player1_id": None, "player2_id": None}}, multi=True)
    # fill values
    for game in db.db_games.Game.find():
        if not game.player1_id:
            game.set_player1(game.nodes[0].get("PB", "?"), game.nodes[0].get("RB", "?"))
        if not game.player2_id:
            game.set_player2(game.nodes[0].get("PW", "?"), game.nodes[0].get("RW", "?"))
        game.save()
