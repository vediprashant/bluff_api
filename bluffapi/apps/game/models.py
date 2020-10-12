from django.db import models

from apps.accounts import models as accounts_models
from apps.common import models as common_models


class Game(common_models.TimeStampModel):
    '''
    Model to store the details of a game
    '''
    started = models.BooleanField(
        default=False, help_text='tells if game is started or not')
    decks = models.PositiveIntegerField(
        default=1, help_text='no of decks in the game from 1-3')
    winner = models.ForeignKey(
        accounts_models.User,
        on_delete=models.CASCADE,
        related_name='winner',
        null=True,
        blank=True,
        help_text='user who won the game'
    )
    owner = models.ForeignKey(accounts_models.User,
                              on_delete=models.CASCADE, related_name='owner', help_text='user which is the owner of this game')

    def __str__(self):
        return f"{self.owner.name}({self.id})"


class GamePlayer(common_models.TimeStampModel):
    '''
    Model to store the details of a player playing a game
    '''
    user = models.ForeignKey(accounts_models.User,
                             on_delete=models.CASCADE, help_text='')
    game = models.ForeignKey(Game, on_delete=models.CASCADE,
                             help_text='game of which gamePlayer is part of')
    player_id = models.PositiveIntegerField(
        null=True, blank=True, help_text='id assigned to a player')
    disconnected = models.BooleanField(
        default=True, help_text='tells if player is disconnected')
    no_action = models.PositiveIntegerField(
        default=0, help_text='no of times no action is performed')
    cards = models.CharField(
        max_length=156, help_text='string of length 156 where 1 is represented by card that user have')

    class Meta:
        unique_together = ('user', 'game')

    def __str__(self):
        return f"{self.user.name} {self.game.id}"


class GameTableSnapshot(common_models.TimeStampModel):
    '''
    Model to store the state of gameTable
    All cards are on Table untill Game has started
    '''
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, help_text='instance of the game')
    current_set = models.PositiveIntegerField(
        null=True, blank=True, help_text='current_set from 1-13')
    cards_on_table = models.CharField(
        max_length=156, help_text='string of length 156 where 1 is represented by card on table')
    last_cards = models.CharField(
        max_length=156, help_text='string of length 156 which represents last cards that were played')
    last_user = models.ForeignKey(
        GamePlayer,
        on_delete=models.CASCADE,
        related_name='last_user',
        null=True,
        help_text='Gamplayer instance whose turn was last'
    )
    current_user = models.ForeignKey(
        GamePlayer,
        on_delete=models.CASCADE,
        related_name='current_user',
        null=True,
        help_text='gamePlayer instance whose turn is current'
    )
    bluff_caller = models.ForeignKey(
        GamePlayer, on_delete=models.CASCADE, blank=True, null=True, related_name='bluff_caller', help_text='gameplayer who called bluff')
    bluff_successful = models.NullBooleanField(
        null=True, help_text='bluff was successful or not')
    did_skip = models.NullBooleanField(
        null=True, help_text='if cureent user skipped his turn')

    def __str__(self):
        return f'{self.game}'
