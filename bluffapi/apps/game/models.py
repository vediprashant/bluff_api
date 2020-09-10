from django.db import models

from apps.accounts import models as accounts_models
from apps.common import models as common_models


class Game(common_models.TimeStampModel):
    """
    Model to store the details of a game
    """
    url = models.CharField(max_length=255)
    inProgress = models.BooleanField(default=False)
    gameStarted = models.BooleanField(default=False)
    winner = models.ForeignKey(
        accounts_models.User, on_delete=models.CASCADE, related_name='winner')
    owner = models.ForeignKey(accounts_models.User,
                              on_delete=models.CASCADE, related_name='owner')

    def __str__(self):
        return f"{self.owner.name} {self.url}"


class GamePlayer(common_models.TimeStampModel):
    """
    Model to store the details of a player playing a game
    """b
    user = models.ForeignKey(accounts_models.User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player_id = models.PositiveIntegerField()
    disconnected = models.BooleanField(default=False)
    noAction = models.PositiveIntegerField(default=0)
    cards = models.BinaryField(max_length=156)

    def __str__(self):
        return f"{self.user.name}"


class GameTableSnapshot(common_models.TimeStampModel):
    """
    Model to store the state of gameTable
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    currentSet = models.PositiveIntegerField()
    cardsOnTable = models.BinaryField(max_length=156)
    lastCards = models.BinaryField(max_length=156)
    lastUser = models.ForeignKey(
        GamePlayer, on_delete=models.CASCADE, related_name='lastUser')
    currentUser = models.ForeignKey(
        GamePlayer, on_delete=models.CASCADE, related_name='currentUser')
    bluffCaller = models.ForeignKey(
        GamePlayer, on_delete=models.CASCADE, blank=True, null=True, related_name='bluffCaller')
    bluffSuccessful = models.NullBooleanField(null=True)
    didSkip = models.NullBooleanField(null=True)

    def __str__(self):
        return f"{self.currentSet} {self.game.url}"
