import random
import sys  # for defining nonce search space
import time
from multiprocessing import Event, Process, Queue
from typing import List, Optional, Union

from cryptography.hazmat.primitives import hashes


class UserState:
    def __init__(self, balance: int, nonce: int):
        """Object representing on-chain state of a user.

        Args:
            balance (int): User's zimcoin balance.
            nonce (int): User's nonce.
        """

        self.balance = balance
        self.nonce = nonce


class Block:
    def __init__(
        self,
        previous: int,
        height: int,
        miner: bytes,
        transactions: List,
        timestamp: int,
        difficulty: int,
        block_id: bytes,
        nonce: int,
    ) -> None:
        """Object representing a block on the blockchain.

        Args:
            previous (int): Block id of the previous block.
            height (int): Number of blocks before this on the chain.
            miner (bytes): Public key hash of the miner responsible for this block.
            transactions (List): A list of transaction objects included in the block.
            timestamp (int): Unix time associated with the blocks creation.
            difficulty (int): Proof-of-work difficulty.
            block_id (bytes): Block id for this block.
            nonce (int): Nonce solution to the proof-of-work puzzle.
        """
        self.previous = previous
        self.height = height
        self.miner = miner
        self.transactions = transactions
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.block_id = block_id
        self.nonce = nonce

    def __str__(self) -> str:
        self.block_id

    @staticmethod
    def concat_txids(transactions: List) -> bytes:
        """A helper function for concatenating transaction ids.

        Args:
            transactions (List): A list of transaction objects.

        Returns:
            bytes: Concatenated transaction ids.
        """
        txids = [t.txid for t in transactions]
        concat = b"".join(txids)

        return concat

    @staticmethod
    def get_block_id(
        previous: bytes,
        miner: bytes,
        transaction_ids: bytes,
        timestamp: int,
        difficulty: int,
        nonce: Optional[int] = None,
    ) -> hashes.Hash:
        """A helper function to create a hash object for a block id. Includes
        functionality to optionally add a nonce so that this can also be used in
        block mining.

        Args:
            previous (bytes): Block id of the previous block in the chain.
            miner (bytes): Public key hash for the block miner.
            transaction_ids (bytes): Concatenated transaction ids included in the block.
            timestamp (int): Unix time associated with this blocks creation.
            difficulty (int): Proof-of-work difficulty.
            nonce (Optional[int], optional): A nonce solution to the proof-of-work puzzle.
                                             Defaults to None.

        Returns:
            hashes.Hash: A hash object for constructing or finalizing a block id.
        """

        to_hash = hashes.Hash(hashes.SHA256())
        to_hash.update(previous)
        to_hash.update(miner)
        to_hash.update(transaction_ids)
        to_hash.update(timestamp.to_bytes(8, byteorder="little", signed=False))
        to_hash.update(difficulty.to_bytes(16, byteorder="little", signed=False))
        if nonce:
            to_hash.update(nonce.to_bytes(8, byteorder="little", signed=False))

        return to_hash

    @staticmethod
    def get_balance_nonce(state: dict, target: bytes) -> int:
        """A helper function to return balance and nonce from a
        dictionary of user states. Includes functionality to deal
        with novel users correctly.

        Args:
            state (dict): A dictionary of user states.
            target (bytes): The public key hash of the user.

        Returns:
            int: balance and nonce of the user.
        """
        try:
            balance = state[target].balance

        # if we have a novel user, return a zero balance and -1 nonce
        except KeyError:
            return 0, -1

        nonce = state[target].nonce

        return balance, nonce

    def verify_and_get_changes(
        self, difficulty: int, previous_user_states: dict
    ) -> dict:
        """Verifies that a block is constructed correctly and that proof-of-work is
        sufficient. Also iterates over included transactions and records changes to
        user states.

        Args:
            difficulty (int): The difficulty of the proof-of-work puzzle used.
            previous_user_states (dict): A dictionary of user states before this block.

        Returns:
            dict: A dictionary with which to update user states.
        """
        # the difficulty of the block should match
        assert self.difficulty == difficulty, f"Incorrect difficulty"

        # block_id should be correct
        txids = Block.concat_txids(self.transactions)
        correct_block_id = Block.get_block_id(
            self.previous,
            self.miner,
            txids,
            self.timestamp,
            self.difficulty,
            self.nonce,
        ).finalize()
        assert (
            self.block_id == correct_block_id
        ), f"Specified block id does not match details"

        # the list of transactions should have a length of 25 or fewer
        assert (
            len(self.transactions) <= 25
        ), f"too many transactions on this block: {len(self.transactions)=} > 25"

        # miner should be 20 bytes
        assert len(self.miner) == 20, f"miner bytes incorrect {len(self.miner)=}"

        # the block_id should be 'small enough' to match the difficulty
        target = 2**256 // self.difficulty
        id_int = int.from_bytes(self.block_id, "big")
        assert id_int <= target, f"Invalid proof of work"

        changes = {}
        block_reward = 10000

        if self.transactions:
            # each transaction should verify correctly then we'll record changes
            for t in self.transactions:

                # changes to sender state
                s_balance, s_nonce = Block.get_balance_nonce(
                    previous_user_states, t.sender_hash
                )
                changes[t.sender_hash] = UserState(s_balance, s_nonce)
                changes[t.sender_hash].balance -= t.amount
                changes[t.sender_hash].nonce += 1

                # changes to recipient state
                r_balance, r_nonce = Block.get_balance_nonce(
                    previous_user_states, t.recipient_hash
                )
                changes[t.recipient_hash] = UserState(r_balance, r_nonce)
                changes[t.recipient_hash].balance += t.amount - t.fee

                block_reward += t.fee

                t.verify(s_balance, s_nonce, False)

                # update between transactions
                previous_user_states.update(changes)

        # additional flat fee for miner or first ever mine
        m_balance, m_nonce = Block.get_balance_nonce(previous_user_states, self.miner)
        changes[self.miner] = UserState(m_balance, m_nonce)
        changes[self.miner].balance += block_reward

        return changes

    def get_changes_for_undo(self, user_states_after: dict) -> dict:
        """Calculates the what should change about UserStates when a block is undone.

        Args:
            user_states_after (dict): The UserStates after this block was confirmed.

        Returns:
            dict: The adjusted UserStates.
        """

        changes = {}
        block_reward = 10000

        if self.transactions:
            for t in self.transactions[::-1]:

                # changes to sender state
                s_balance, s_nonce = Block.get_balance_nonce(
                    user_states_after, t.sender_hash
                )

                changes[t.sender_hash] = UserState(s_balance, s_nonce)
                changes[t.sender_hash].balance += t.amount
                changes[t.sender_hash].nonce -= 1

                # changes to recipient hash
                r_balance, r_nonce = Block.get_balance_nonce(
                    user_states_after, t.recipient_hash
                )

                changes[t.recipient_hash] = UserState(r_balance, r_nonce)
                changes[t.recipient_hash].balance += t.fee - t.amount

                block_reward += t.fee

                # update between transactions
                user_states_after.update(changes)

        m_balance, m_nonce = Block.get_balance_nonce(user_states_after, self.miner)
        changes[self.miner] = UserState(m_balance, m_nonce)
        changes[self.miner].balance -= block_reward

        return changes


def mine_block(
    previous: bytes,
    height: int,
    miner: bytes,
    transactions: List,
    timestamp: int,
    difficulty: int,
    cuttoff_time: int,
    min_int: int = 0,
    max_int: int = sys.maxsize,
) -> Union[Block, None]:
    """A Zimcoin block mining function. Miner searches for an acceptable nonce for an unmined block
    or until the cutoff time is reached. This miner keeps track of guesses to avoid repeating nonce
    hashing, and allows for defining the integer search space as a range.

    Args:
        previous (bytes): Block id for the previous block in this chain.
        height (int): The number of blocks before this on the chain.
        miner (bytes): Public key hash of the user mining this block.
        transactions (List): A list of transaction objects to include in this block.
        timestamp (int): Unix time.
        difficulty (int): Difficulty of the proof-of-work puzzle.
        cutoff_time (int): Timestamp when the miner will stop working and return None.
        min_int (int, optional): Lower bound of the search space for this miner. Defaults to 0.
        max_int (int, optional): Upper bound of the search space for this miner. Defaults to sys.maxsize.


    Returns:
        Union[Block, None]: A Block object including an acceptable proof-of-work nonce or None
        if cutoff time is reached before a solution.
    """

    # concatenate txids and get the block id hash object without nonce
    txids = Block.concat_txids(transactions)
    to_hash = Block.get_block_id(previous, miner, txids, timestamp, difficulty)
    target = 2**256 // difficulty

    # define an initial guess just above the target
    guess = target + 1

    # initialize a set to hold guesses already attempted
    tried = set()

    def make_guess(tried: set, min_int: int, max_int: int) -> Union[set, bytes, None]:
        """A helper function for generating a randomized nonce guess. Includes
        behavior for avoiding repeating guesses.

        Args:
            tried (set): A collection of guesses already attempted.
            max_int (int, optional): Upper range for guesses. Defaults to sys.maxsize.

        Returns:
            Union[set, bytes]: The attempted set and random guess.
        """
        n = random.randint(min_int, max_int)

        # if we somehow generate a repeat, call recursively until we don't
        if n in tried:
            make_guess(tried)
            sys.exit(0)

        # update our running attempts set
        tried.add(n)

        return tried, n

    # assign initial values to nonce guess and finalized block_id
    n = 0
    attempt = to_hash

    while guess > target:
        if time.time() < cuttoff_time:
            # single-process mining loop
            tried, n = make_guess(tried, min_int=min_int, max_int=max_int)
            attempt = to_hash.copy()
            attempt.update(n.to_bytes(8, byteorder="little", signed=False))
            attempt = attempt.finalize()
            guess = int.from_bytes(attempt, byteorder="big", signed=False)
        else:
            return None

    zimblock = Block(
        previous, height, miner, transactions, timestamp, difficulty, attempt, n
    )

    return zimblock


def search_loop(event: Event, queue: Queue, mine_args: dict) -> None:
    """Search loop used in conjunction with mp_coordinator."""
    while True:
        zim = mine_block(**mine_args)
        if zim:
            queue.put(zim)
            event.set()
        else:
            queue.put(None)
            event.set()


def mp_coordinator(
    previous: bytes,
    height: int,
    miner: bytes,
    transactions: List,
    timestamp: int,
    difficulty: int,
    cutoff_time: int,
    processes: int = 4,
    min_int: int = 30_000_000_000
) -> Union[Block, None]:
    """A coordinating function for a multi-process mining strategy. This orchestrates
    spawning a group of miner workers using the designated cutoff time, and by dividing
    a search space defined by 2 * a 64-bit pointer value amongst the workers such that they
    work on just a slice of the total search space, avoiding repeat nonce guessing.

    Args:
        previous (bytes): Block id for the previous block in this chain.
        height (int): The number of blocks before this on the chain.
        miner (bytes): Public key hash of the user mining this block.
        transactions (List): A list of transaction objects to include in this block.
        timestamp (int): Unix time.
        difficulty (int): Difficulty of the proof-of-work puzzle.
        cutoff_time (int): Timestamp when miners will stop working and return None.
        processes (int, optional): Number of processes to run. Defaults to 8.

    Returns:
        Block: A Block object including an acceptable proof-of-work nonce.
    """

    workers = []

    mine_args = {
        "previous": previous,
        "height": height,
        "miner": miner,
        "transactions": transactions,
        "timestamp": timestamp,
        "difficulty": difficulty,
        "cutoff_time": cutoff_time,
        "min_int": min_int,
        "max_int": None,
    }

    # define an event to track solution status across processes
    event = Event()

    # define a queue to hold a solution when reached
    queue = Queue(maxsize=1)

    # define search space
    space = sys.maxsize * 2

    # size of space each worker will be constrained to
    w_slice = (space - min_int) // processes

    # spawn processes
    for worker in range(processes):
        mine_args["min_int"] = (w_slice * worker) + min_int
        mine_args["max_int"] = (w_slice * (worker + 1)) + min_int
        p = Process(target=search_loop, args=(event, queue, mine_args))
        p.start()
        workers.append(p)

    # loop that runs until the event is set (block mined or cutoff reached)
    while True:
        if event.is_set():

            # grab our solution
            result = queue.get()

            # sigterm processes
            for w in workers:
                w.terminate()

            return result
