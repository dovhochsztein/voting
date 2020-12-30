import random
import numpy as np
import itertools
import time

class Vote:
    def __init__(self, number_of_alternatives, randomizer_fn):
        ranking = randomizer_fn(number_of_alternatives)
        self.ranking = ranking
    def prefers(self, first_alternative, second_alternative):
        ranking = self.ranking
        if first_alternative in ranking and second_alternative in ranking:
            if ranking.index(first_alternative) < ranking.index(second_alternative):
                return True
        return False


def randomizer_1(number_of_alternatives):
    number_to_rank = random.randint(1, number_of_alternatives)
    ranking = random.sample(list(range(number_of_alternatives)), number_to_rank)
    return ranking



class Election_Profile:
    def __init__(self, number_of_votes, number_of_alternatives, randomizer_fn):
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
            sub_lists.extend(list(itertools.combinations(range(number_of_alternatives), ii)))
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

def check_iia(voting_system, election):
    number_of_alternatives = election.number_of_alternatives
    sub_lists = election.sub_lists
    society_ranking = voting_system(election.rankings, list(range(number_of_alternatives)))
    for sub_list in sub_lists:
        new_society_ranking = voting_system(simplify(election.rankings, sub_list), list(sub_list))
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
N = 10000
iia = np.full(N, False)
for ii in range(N):
    election = Election_Profile(1000, 5, randomizer_1)
    # print(election)
    iia[ii] = check_iia(fptp, election)
    check_unanimity(fptp, election)
print(sum(iia)/N)
print(time.time() - now)