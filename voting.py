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
    """
    Randomizer that generates only rankings that obey the coalition rule:
    A coalition voter has all coalition members consecutively in their order of
    preference. E.g. a voter considers two coalitions (0 and 1) with 2 and 3
    alternatives, respectively (coalition 0 has alternatives 0, 1 and coalition 1
    has alternatives 2, 3, 4).
    The following are valid rankings:
    - 1, 2, 3
    - 0, 3
    - 2, 3, 0, 1
    - 3, 4, 2, 1, 0
    - 1,
    While the following rankings are invalid for a coalition voter:
    - 0, 4, 1
    - 2, 1, 3
    """
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
        # print(alternatives_to_rank, ranking)
        # print(time.time() - start)
        return ranking

B = CoalitionRandomizer([4, 3, 2], 'uniform')


class Vote:
    """
    Class for a single vote object. Automatically generates a ranking on
    instantiation based on a generator function.
    """
    def __init__(self, randomizer: Randomizer):
        ranking = randomizer.generate_rank()
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


class Election_Profile:

    """
    Class for election profile, all Vote objects are created on instantiation.
    """
    def __init__(self, number_of_votes: int, randomizer: Randomizer):
        self.votes = []
        self.rankings = []
        self.number_of_alternatives = randomizer.number_of_alternatives
        self.number_of_votes = number_of_votes
        for ii in range(number_of_votes):
            new_vote = Vote(randomizer)
            self.votes.append(new_vote)
            self.rankings.append(new_vote.ranking)

        self.sub_lists = []
        for ii in range(2, self.number_of_alternatives):
            self.sub_lists.extend(set(itertools.combinations(range(self.number_of_alternatives), ii)))

    def simplify(self, remaining_alternatives):
        simplified_rankings = []
        for ranking in self.rankings:
            new_ranking = [value for value in ranking if value in remaining_alternatives]
            simplified_rankings.append(new_ranking)
        return simplified_rankings

    def __str__(self):
        return str(self.rankings)


class EvaluationProcedure:
    def __init__(self, first_place_only: bool = False, instant_runoff = False):
        self.first_place_only = first_place_only
        self.instant_runoff = instant_runoff

    def __name__(self):
        name = self.__class__.__name__
        if self.first_place_only:
            name += '; first place only'
        if self.instant_runoff:
            name += '; instant runoff'
        return f'"{name}"'

    def evaluate(self, rankings: list[list], list_of_alternatives: list):
        if len(list_of_alternatives) == 1:
            return [list_of_alternatives[0]]
        society_ranking = self.get_society_ranking(rankings,
                                                   list_of_alternatives)
        if self.instant_runoff:
            if len(list_of_alternatives) == 2:
                return society_ranking[0:1]
            else:
                list_of_alternatives = society_ranking[:-1]
                rankings = simplify(rankings, list_of_alternatives)
                return self.evaluate(rankings, list_of_alternatives)
        else:
            if self.first_place_only:
                return society_ranking[0:1]
            else:
                return society_ranking

    def get_society_ranking(self, rankings: list[list],
                                  list_of_alternatives: list):
        pass


class FirstPastThePost(EvaluationProcedure):
    def __init__(self, first_place_only: bool = False, instant_runoff=False):
        super().__init__(first_place_only, instant_runoff)

    def get_society_ranking(self, rankings: list[list], list_of_alternatives: list):
        list_of_alternatives = np.array(list_of_alternatives)
        vote_totals = np.zeros((len(list_of_alternatives)))
        for ranking in rankings:
            if len(ranking) > 0:
                vote_totals[np.where(list_of_alternatives == ranking[0])] += 1
        society_ranking = list_of_alternatives[np.flip(np.argsort(vote_totals))]
        if self.first_place_only:
            return society_ranking[0:1]
        else:
            return society_ranking


class InstantRunoff(FirstPastThePost):
    def __init__(self, first_place_only: bool = False, instant_runoff=False):
        super().__init__(first_place_only, instant_runoff)


class BordaCount(EvaluationProcedure):
    def __init__(self, first_place_only: bool = False, instant_runoff=False):
        super().__init__(first_place_only, instant_runoff)

    def borda_score(self, index, number_of_alternatives):
        return number_of_alternatives - index

    def evaluate(self, rankings: list[list], list_of_alternatives: list):
        if len(list_of_alternatives) == 1:
            return [list_of_alternatives[0]]
        borda_score = {ii: 0 for ii in list_of_alternatives}
        number_of_alternatives = len(list_of_alternatives)
        for ranking in rankings:
            for index, alternative in enumerate(ranking):
                borda_score[alternative] +=\
                    self.borda_score(index, number_of_alternatives)
        society_ranking = [key for key, value in
                           sorted(borda_score.items(),
                                  key=lambda item: item[1],
                                  reverse=True)]
        if self.first_place_only:
            return society_ranking[:1]
        else:
            return society_ranking


class TournamentStyleBordaCount(BordaCount):
    def __init__(self, first_place_only: bool = False, instant_runoff=False):
        super().__init__(first_place_only, instant_runoff)

    def borda_score(self, index, number_of_alternatives):
        return number_of_alternatives - index - 1


class DowdallBordaCount(BordaCount):
    def __init__(self, first_place_only: bool = False, instant_runoff=False):
        super().__init__(first_place_only, instant_runoff)

    def borda_score(self, index, number_of_alternatives):
        return 1 / (index + 1)




class Axiom:
    def __init__(self, first_place_only: bool = True):
        self.first_place_only = first_place_only

    def check_axiom(self, election: Election_Profile,
                    evaluation_procedure: EvaluationProcedure):
        pass


class IndependenceOfIrrelevantAlternatives(Axiom):
    def __init__(self, first_place_only: bool = True):
        super().__init__(first_place_only)

    def check_axiom(self, election: Election_Profile,
                    evaluation_procedure: EvaluationProcedure):
        number_of_alternatives = election.number_of_alternatives
        society_ranking =\
            evaluation_procedure.evaluate(election.rankings,
                                          list(range(number_of_alternatives)))
        sub_lists = election.sub_lists
        if self.first_place_only:
            sub_lists = [ii for ii in sub_lists if society_ranking[0] in ii]
        for sub_list in sub_lists:
            new_society_ranking = evaluation_procedure.evaluate(
                simplify(election.rankings, sub_list), list(sub_list))
            if not check_maintains_order(new_society_ranking, society_ranking, self.first_place_only):
                print(f'{evaluation_procedure.__name__()} Failed IIA: Ranking with all was {society_ranking}, but the ranking with only the alternatives {sub_list} is {new_society_ranking}')
                return False
        return True


def check_maintains_order(small_list, large_list, first_place_only):
    if first_place_only:
        return small_list[0] == large_list[0]
    else:
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
N = 200
fptp_axiom_results = np.full(N, False)
ir_axiom_results = np.full(N, False)
borda_axiom_results = np.full(N, False)
borda_ir_axiom_results = np.full(N, False)
tournament_borda_axiom_results = np.full(N, False)
dowdall_borda_axiom_results = np.full(N, False)
number_candidates = 4
randomizer = Randomizer(number_candidates, 'uniform')
fptp = FirstPastThePost()
ir = InstantRunoff()
borda = BordaCount()
borda_ir = BordaCount(instant_runoff=True)
tournament_borda = TournamentStyleBordaCount()
dowdall_borda = DowdallBordaCount()

iia = IndependenceOfIrrelevantAlternatives()
for ii in range(N):
    election = Election_Profile(1000, randomizer)
    fptp_result = fptp.evaluate(election.rankings, list(range(number_candidates)))
    ir_result = ir.evaluate(election.rankings, list(range(number_candidates)))
    borda_result = borda.evaluate(election.rankings, list(range(number_candidates)))
    borda_ir_result = borda_ir.evaluate(election.rankings, list(range(number_candidates)))
    tournament_borda_result = tournament_borda.evaluate(election.rankings, list(range(number_candidates)))
    dowdall_borda_result = dowdall_borda.evaluate(election.rankings, list(range(number_candidates)))
    fptp_axiom_results[ii] = iia.check_axiom(election, fptp)
    ir_axiom_results[ii] = iia.check_axiom(election, ir)
    borda_axiom_results[ii] = iia.check_axiom(election, borda)
    borda_ir_axiom_results[ii] = iia.check_axiom(election, borda_ir)
    print(borda_result == borda_ir_result, borda_axiom_results[ii] == borda_ir_axiom_results[ii])
    tournament_borda_axiom_results[ii] = iia.check_axiom(election, tournament_borda)
    dowdall_borda_axiom_results[ii] = iia.check_axiom(election, dowdall_borda)
    print('-----------')
    # print(election)
    # results[ii] = check_iia(fptp, election)
    # check_unanimity(fptp, election)
print(f'FPTP satisfies IIA {100 * sum(fptp_axiom_results) / N}% of the time')
print(f'IR satisfies IIA {100 * sum(ir_axiom_results) / N}% of the time')
print(f'Borda satisfies IIA {100 * sum(borda_axiom_results) / N}% of the time')
print(f'Borda IR satisfies IIA {100 * sum(borda_ir_axiom_results) / N}% of the time')
print(f'Tournament Borda satisfies IIA {100 * sum(tournament_borda_axiom_results) / N}% of the time')
print(f'Dowdall Borda satisfies IIA {100 * sum(dowdall_borda_axiom_results) / N}% of the time')
print(time.time() - now)