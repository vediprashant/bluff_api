from django.db import models

from apps.accounts import models as accounts_models
from apps.common import models as common_models


class Game(common_models.TimeStampModel):
    """
    Model to store the details of a game
    """
    started = models.BooleanField(default=False)
    decks = models.PositiveIntegerField(default=1)
    winner = models.ForeignKey(
        accounts_models.User,
        on_delete=models.CASCADE,
        related_name='winner',
        null=True,
    )
    owner = models.ForeignKey(accounts_models.User,
                              on_delete=models.CASCADE, related_name='owner')

    def __str__(self):
        return f"{self.owner.name}({self.id})"


class GamePlayer(common_models.TimeStampModel):
    """
    Model to store the details of a player playing a game
    """
    user = models.ForeignKey(accounts_models.User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player_id = models.PositiveIntegerField(null=True, blank=True)
    disconnected = models.BooleanField(default=True)
    noAction = models.PositiveIntegerField(default=0)
    cards = models.CharField(max_length=156)

    def __str__(self):
        return f"{self.user.name}"


class GameTableSnapshot(common_models.TimeStampModel):
    """
    Model to store the state of gameTable
    All cards are on Table untill Game has started
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    currentSet = models.PositiveIntegerField(null=True, blank=True)
    cardsOnTable = models.CharField(max_length=156)
    lastCards = models.CharField(max_length=156)
    lastUser = models.ForeignKey(
        GamePlayer,
        on_delete=models.CASCADE,
        related_name='lastUser',
        null=True,
    )
    currentUser = models.ForeignKey(
        GamePlayer,
        on_delete=models.CASCADE,
        related_name='currentUser',
        null=True,
    )
    bluffCaller = models.ForeignKey(
        GamePlayer, on_delete=models.CASCADE, blank=True, null=True, related_name='bluffCaller')
    bluffSuccessful = models.NullBooleanField(null=True)
    didSkip = models.NullBooleanField(null=True)

    def __str__(self):
        return f"{self.game}"
