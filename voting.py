import random
import numpy as np
import itertools
import time
from typing import Union, Callable

# todo for architecture: Class for Axioms - base class has blank checker method,
#  subclasses have implements checker methods. include flag for check
#  class for randomizer, subclasses for different ways (subclasses for uniform,
#  coalition voter, etc)
#  class for election profile, method to evaluate with different ways
#  class for results evaluation, subclasses for different ways (fptp, bordas, instant runoffs)


class Vote:
    """
    Class for a single vote object. Automatically generates a ranking on
    instantiation based on a generator function.
    """
    def __init__(self, number_of_alternatives, randomizer_fn):
        ranking = randomizer_fn(number_of_alternatives)
        self.ranking = ranking
        self.preference_cache = dict()

    def first_choice(self, removed_alternatives: Union[set, None] = None):
        """
        Gives the first choice of a voter.
        :param removed_alternatives:
        :return:
        """
        if removed_alternatives is None:
            removed_alternatives = set()
        choice = None
        for alternative in self.ranking:
            if alternative not in removed_alternatives:
                choice = alternative
                break
        return choice

    def prefers(self, first_alternative, second_alternative):
        """
        checks preference between first and second alternatives
        returns True if first is preferred, False if second, None if no preferrence
        """
        if (first_alternative, second_alternative) in self.preference_cache:
            return self.preference_cache[
                (first_alternative, second_alternative)]
        ranking = self.ranking
        if first_alternative in ranking and second_alternative in ranking:
            if ranking.index(first_alternative) < \
                    ranking.index(second_alternative):
                self.preference_cache[
                    (first_alternative, second_alternative)] = True
                return True
        else:
            if first_alternative in ranking:
                self.preference_cache[
                    (first_alternative, second_alternative)] = True
                return True
            elif second_alternative in ranking:
                self.preference_cache[
                    (first_alternative, second_alternative)] = False
                return True
            else:
                self.preference_cache[
                    (first_alternative, second_alternative)] = None
                return None


class Randomizer:
    """
    Base class for randomizer object to generate a voter ranking. Default
    generate method assumes a uniform distribution.
    """
    def __init__(self, number_of_alternatives: int = 2, number_to_rank_funx: Union[Callable, str, None] = None):
        self.number_of_alternatives = number_of_alternatives
        if number_to_rank_funx is None:
            self.number_to_rank_funx = lambda: self.number_of_alternatives
        elif type(number_to_rank_funx) is str:
            if number_to_rank_funx == 'all':
                self.number_to_rank_funx = lambda: self.number_of_alternatives
            elif number_to_rank_funx == 'uniform':
                self.number_to_rank_funx =\
                    lambda: random.randint(1, self.number_of_alternatives)
        else:
            self.number_to_rank_funx = number_to_rank_funx

    def generate_rank(self):
        number_to_rank = self.number_to_rank_funx()
        ranking = random.sample(list(range(self.number_of_alternatives)),
                                number_to_rank)
        return ranking

A = Randomizer(5, 'uniform')


class CoalitionRandomizer(Randomizer):
    def __init__(self, coalition_sizes: list, number_to_rank_funx: Union[Callable, str, None] = None):
        number_of_alternatives = sum(coalition_sizes)
        self.coalition_sizes = coalition_sizes
        super().__init__(number_of_alternatives, number_to_rank_funx)
        self.coalition_to_alternative_dict = {}
        self.alternative_to_coalition_dict = {}
        index = 0
        for coalition, size in enumerate(coalition_sizes):
            self.coalition_to_alternative_dict[coalition] = range(index, index + size)
            for alternative in range(index, index + size):
                self.alternative_to_coalition_dict[alternative] = coalition
            index += size

    def generate_rank(self):
        start = time.time()
        number_to_rank = self.number_to_rank_funx()
        alternatives_to_rank = random.sample(list(range(self.number_of_alternatives)),
                                number_to_rank)
        coalitions_to_rank = dict()
        for alternative in alternatives_to_rank:
            coalition = self.alternative_to_coalition_dict[alternative]
            if coalition not in coalitions_to_rank:
                coalitions_to_rank[coalition] = set()
            coalitions_to_rank[coalition].add(alternative)

        coalition_order = list(coalitions_to_rank.keys())
        random.shuffle(coalition_order)
        ranking = list()
        for coalition in coalition_order:
            alternatives = list(coalitions_to_rank[coalition])
            random.shuffle(alternatives)
            ranking.extend(alternatives)
        print(alternatives_to_rank, ranking)
        print(time.time() - start)
        return ranking

B = CoalitionRandomizer([4, 3, 2], 'uniform')

def randomizer_1(number_of_alternatives):
    number_to_rank = random.randint(1, number_of_alternatives)
    ranking = random.sample(list(range(number_of_alternatives)), number_to_rank)
    return ranking



class Election_Profile:
    """
    Class for election profile, all Vote objects are created on instantiation.
    """
    def __init__(self, number_of_votes: int, number_of_alternatives: int,
                 randomizer_fn: Callable):
        self.votes = []
        self.rankings = []
        self.number_of_alternatives = number_of_alternatives
        self.number_of_votes = number_of_votes
        for ii in range(number_of_votes):
            new_vote = Vote(number_of_alternatives, randomizer_fn)
            self.votes.append(new_vote)
            self.rankings.append(new_vote.ranking)

        sub_lists = []
        for ii in range(2, number_of_alternatives):
            sub_lists.extend(set(itertools.combinations(range(number_of_alternatives), ii)))
        self.sub_lists = sub_lists

    def simplify(self, remaining_alternatives):
        simplified_rankings = []
        for ranking in self.rankings:
            new_ranking = [value for value in ranking if value in remaining_alternatives]
            simplified_rankings.append(new_ranking)
        return simplified_rankings

    def __str__(self):
        return str(self.rankings)


def fptp(rankings, list_of_alternatives):
    list_of_alternatives = np.array(list_of_alternatives)
    vote_totals = np.zeros((len(list_of_alternatives)))
    for ranking in rankings:
        if len(ranking) > 0:
            vote_totals[np.where(list_of_alternatives == ranking[0])] += 1
    society_ranking = list_of_alternatives[np.flip(np.argsort(vote_totals))]
    # winners = np.where(vote_totals == np.max(vote_totals))
    # winner = winners[0][0]
    return society_ranking


class Axiom:
    def __init__(self, check_function):
        self.check_function = check_function

    def check_axiom(self, election, voting_system):
        pass

def check_iia(voting_system, election, check_all=True):
    number_of_alternatives = election.number_of_alternatives
    sub_lists = election.sub_lists
    society_ranking = voting_system(election.rankings, list(range(number_of_alternatives)))
    for sub_list in sub_lists:
        if not check_all and society_ranking[0] not in sub_list:
            continue
        new_society_ranking = voting_system(simplify(election.rankings, sub_list), list(sub_list))
        print(new_society_ranking)
        if not check_maintains_order(new_society_ranking, society_ranking):
            # print(f'IIA Failed: Ranking with all was {society_ranking}, but the ranking with only the alternatives {sub_list} is {new_society_ranking}')
            return False
    # print('IIA Satisfied')
    return True


def check_maintains_order(small_list, large_list):
    index = 0
    for element in large_list:
        if small_list[index] == element:
            index += 1
            if index == len(small_list):
                return True
    return False


def simplify(rankings, remaining_alternatives):
    simplified_rankings = []
    for ranking in rankings:
        new_ranking = [value for value in ranking if value in remaining_alternatives]
        simplified_rankings.append(new_ranking)
    return simplified_rankings


def prefers(ranking, first_alternative, second_alternative):
    ranking = list(ranking)
    if first_alternative in ranking and second_alternative in ranking:
        if ranking.index(first_alternative) < ranking.index(second_alternative):
            return True
    return False


def check_unanimity(voting_system, election):
    number_of_alternatives = election.number_of_alternatives
    sub_lists = election.sub_lists
    society_ranking = voting_system(election.rankings, list(range(number_of_alternatives)))
    for sub_list in sub_lists:
        if len(sub_list) == 2:
            if prefers(society_ranking, sub_list[0], sub_list[1]):
                all_unhappy = True
                for ranking in election.rankings:
                    if not prefers(ranking, sub_list[1], sub_list[0]):
                        all_unhappy = False
                        break
                if all_unhappy:
                    # print(f'Unanimnity Failed: Everyone preferred {sub_list[1]} over {sub_list[0]} but society chose {society_ranking},')
                    return False
            elif prefers(society_ranking, sub_list[1], sub_list[1]):
                all_unhappy = True
                for ranking in election.rankings:
                    if not prefers(ranking, sub_list[0], sub_list[1]):
                        all_unhappy = False
                        break
                if all_unhappy:
                    # print(f'Unanimnity Failed: Everyone preferred {sub_list[0]} over {sub_list[1]} but society chose {society_ranking},')
                    return False
    # print('Unanimity Satisfied')
    return True

now = time.time()
N = 100
iia = np.full(N, False)
for ii in range(N):
    election = Election_Profile(1000, 5, randomizer_1)
    # print(election)
    iia[ii] = check_iia(fptp, election)
    check_unanimity(fptp, election)
print(sum(iia)/N)
print(time.time() - now)