import argparse
import numpy as np
from scipy.stats import beta
from matplotlib import pyplot as plt


# create a global voter_reputation of random size 
voter_reputation = np.zeros((1000, 1000))
index = 0
harshness = 10

class Voter:
    def __init__(self, id, expertise_areas, stake):
        self.id = id
        self.reputation = 1.0
        self.expertise_areas = expertise_areas
        self.stake = stake  # Add stake for PoS
        self.alpha = 1  # Parameters for Beta distribution
        self.beta = 1

class Vote:
    def __init__(self, voter, news_item, vote):
        self.voter = voter
        self.news_item = news_item
        self.vote = vote

class NewsItem:
    def __init__(self, id, content, area):
        self.id = id
        self.content = content
        self.area = area
        self.votes = []
        self.truth = None

    def add_vote(self, vote):
        self.votes.append(vote)

    def evaluate_votes(self):
        # Modify the weighted sum to include the stake
        weighted_sum = sum(vote.vote * vote.voter.reputation * vote.voter.stake for vote in self.votes)
        
        # Modify the total reputation to include the stake
        total_reputation = sum(vote.voter.reputation * vote.voter.stake for vote in self.votes)
        
        final_result = weighted_sum / total_reputation
        final_decision = 1 if final_result > 0.5 else 0
        update_reputation(self, final_decision)
        return final_decision
    
    def harsh_evaluate(self, truth_value):
        global index
        for vote in self.votes:
            if vote.vote == truth_value:
                vote.voter.alpha += harshness
            else:
                vote.voter.beta += harshness
            vote.voter.reputation = beta.mean(vote.voter.alpha, vote.voter.beta)
            # use global index 
            voter_reputation[index][vote.voter.id] = vote.voter.reputation
        index += 1
    

# store the reputation at each time_stamp for each user in global numpy array of size (Ni, N)
def update_reputation(news_item, true_value):
    global index
    for vote in news_item.votes:
        if vote.vote == true_value:
            vote.voter.alpha += 1
        else:
            vote.voter.beta += 1
        vote.voter.reputation = beta.mean(vote.voter.alpha, vote.voter.beta)
        voter_reputation[index][vote.voter.id] = vote.voter.reputation
    index += 1



def print_results(news_items):
    # print the votes array for each news_item 
    for news_item in news_items:
        # print id and truth value of news item
        print("News Item", news_item.id, "Truth", news_item.truth)
        for vote in news_item.votes:
            print("Voter", vote.voter.id, "Vote", vote.vote)

def simulate(N,p, q, Ni):
    # create a list of N nodes with q fraction malicious 
    # and p fraction benign with correct vote probability 0.9
    # and 1-p fraction benign with correct vote probability 0.7 
    # use numpy to use bernoullie distribution to generate the votes 

    # initialize the votes array

    # print voter repuation size 
    print("Voter Reputation Size: ", voter_reputation.shape)

    # create N voters with expertise areas and stake=1
    voters = []
    for i in range(N):
        expertise_areas = np.random.randint(0, 10, 5)
        stake = 1
        voters.append(Voter(i, expertise_areas, stake))
    
    # create news items with random content and area in a while loop
    i = 0
    while True:
        content = np.random.randint(0, 2, 100)
        area = np.random.randint(0, 10)
        news_item = NewsItem(i, content, area)

        # assign random truth value to the news item
        news_item.truth = np.random.randint(0, 2)

        # cast malicious vote (vote opposite to truth value) of first q fraction of voters
        for j in range(int(q*N)):
            vote = Vote(voters[j], news_item, 1-news_item.truth)
            news_item.add_vote(vote)

        # cast correct vote with probability 0.9 for next p fraction of voters
        for j in range(int(q*N), int((q+ (1-q)*p)*N)):
            # Generate a Bernoulli distributed random number with p=0.9
            bernoulli_num = np.random.binomial(1, 0.9)

            # If the Bernoulli number is 1, cast a correct vote
            if bernoulli_num == 1:
                vote = Vote(voters[j], news_item, news_item.truth)
            # Otherwise, cast an incorrect vote
            else:
                vote = Vote(voters[j], news_item, not news_item.truth)

            news_item.add_vote(vote)

        # cast correct vote with probability 0.7 for the rest of the voters
        for j in range(int((q+ (1-q)*p)*N), N):
            # Generate a Bernoulli distributed random number with p=0.7
            bernoulli_num = np.random.binomial(1, 0.7)

            # If the Bernoulli number is 1, cast a correct vote
            if bernoulli_num == 1:
                vote = Vote(voters[j], news_item, news_item.truth)
            # Otherwise, cast an incorrect vote
            else:
                vote = Vote(voters[j], news_item, not news_item.truth)
            # vote = Vote(voters[j], news_item, not news_item.truth)

            news_item.add_vote(vote)
        # print("News Item", news_item.id, "Truth", news_item.truth)
        # print the votes array for each news_item
        # for vote in news_item.votes:
        #     print("Voter", vote.voter.id, "Vote", vote.vote)


        # update_reputation(news_item, final_decision)
        if i % (N//10) == 0 and harshness != 0:
            # here call harsh evaluate and send truth_value 
            news_item.harsh_evaluate(news_item.truth)
        else: 
            # here call evaluate votes and send the final decision 
            news_item.evaluate_votes()

        i += 1

        # break when i = 20
        if i == Ni:
            break

    # calculate 3 trustworthiness score by aggregating reputation scores of each voters and print first q fraction, then (1-q)p franction then (1-q)(1-p) fraction 
    trustworthiness_scores = []
    # Calculate the trustworthiness score for the first q fraction of voters
    trustworthiness_scores.append(sum(voter.reputation for voter in voters[:int(q*N)]))
    # Calculate the trustworthiness score for the next (1-q)p fraction of voters
    trustworthiness_scores.append(sum(voter.reputation for voter in voters[int(q*N):int((q+p)*N)]))
    # Calculate the trustworthiness score for the last (1-q)(1-p) fraction of voters
    trustworthiness_scores.append(sum(voter.reputation for voter in voters[int((q+p)*N):]))

    # divide trustworthiness score by sum of reputation scores of all voters
    trustworthiness_scores = [score / sum(voter.reputation for voter in voters) for score in trustworthiness_scores]

    # print the trustworthiness scores
    # print("Trustworthiness Scores")
    # print("First q fraction of voters:", trustworthiness_scores[0])
    # print("Next (1-q)p fraction of voters 0.9:", trustworthiness_scores[1])
    # print("Last (1-q)(1-p) fraction of voters 0.7:", trustworthiness_scores[2])


    # Calculate avg of first q fraction, then (1-q)p franction then (1-q)(1-p) fraction, try to avoid int values use float values 
    avg_reputation_scores = []
    # Calculate the average reputation score for the first q fraction of voters
    avg_reputation_scores.append(sum(voter.reputation for voter in voters[:int(q*N)]) / int(q*N))
    # Calculate the average reputation score for the next (1-q)p fraction of voters
    avg_reputation_scores.append(sum(voter.reputation for voter in voters[int(q*N): int((q*N)) +int ((1-q)*p*N)]) / int ((1-q)*p*N))
    # Calculate the average reputation score for the last (1-q)(1-p) fraction of voters
    avg_reputation_scores.append(sum(voter.reputation for voter in voters[ int((q*N)) +int ((1-q)*p*N) :]) / (N - int((q*N)) -int ((1-q)*p*N)))

    

    # print q*N, (1-q)*p*N, (1-q)*(1-p)*N and q+p)*N 


    # print the avg reputation scores
    print("Average Reputation Scores")
    print(f"First {int( q*N)} fraction of voters:", avg_reputation_scores[0])
    print(f"Next {int((1-q)*p*N)} fraction of voters 0.9:", avg_reputation_scores[1])
    print(f"Last {N - int((q*N)) -int ((1-q)*p*N)} fraction of voters 0.7:", avg_reputation_scores[2])



    # print the reputation scores of all voters 
    for i in range(N):
        print("Voter", i, "Reputation", voters[i].reputation)


    


def draw_results(N, p, q, Ni):
    # using matplotlib show how the reputation scores of all voters change over time in the same plot 
    plt.figure(figsize=(10,6))
    for i in range(voter_reputation.shape[1]):
        plt.plot(voter_reputation[:, i])
    plt.xlabel("Time")
    plt.ylabel("Reputation Score")
    plt.title(f"Reputation Score for for N={N} voters Over Time for p={p}, q={q}, Ni={Ni}, harshness={harshness}")
    plt.tight_layout()
    plt.savefig("result.jpg")


# start main, and run the main loop

if __name__ == "__main__":
    # use argparse to get float p, float q, integer N 
    parser = argparse.ArgumentParser(description='Fake News Detection')
    parser.add_argument('--N', type=int, help='Number of Voters', default=10)
    parser.add_argument('--q', type=float, help='Fraction of Malicious', default=0.3)
    parser.add_argument('--p', type=float, help='Fraction of Benigh with correct vote prob 0.9', default=0.5)
    # number of news items as Ni set default = 1000 
    parser.add_argument('--Ni', type=int, help='Number of News Items', default=1000)
    # new integer parameter of harshness with default value = 10 
    parser.add_argument('--harshness', type=int, help='Harshness', default=10)

    args = parser.parse_args() 
    p = args.p
    q = args.q
    N = args.N
    Ni = args.Ni
    harshness = args.harshness
    # print the values of p, q, N, Ni 

    # print size of voter_reputation array

    # access global voter_reputation array and set it to zeros of size (Ni, N)
    voter_reputation = np.zeros((Ni, N))

    print("Simulating for : Total : " +str(N) + " voters, "  + str(int(q*N)) + "  Malicious Voters,"  + " and, " + str(int ((1-q)*p*N)) + " Benign Voters with correct vote probability 0.9, and " + str(N - int((q*N)) -int ((1-q)*p*N)) + " Benign Voters with correct vote probability 0.7, for " + str(Ni) + " News Items, with harshness " + str(harshness) )

    simulate(N,p,q, Ni)
    # print the results of the simulation draw the graph of reputation scores of all voters 
    draw_results(N,p,q, Ni)

