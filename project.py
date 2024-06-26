import simpy
import random
import pandas as pd

# Constants for the simulation
PROCESSING_TIMES = {'loading': 5, 'machining': 10, 'assembling': 8, 'inspecting': 6, 'packaging': 4}
MAINTENANCE_TIME = 3
BREAKDOWN_RATE = 0.1  # Probability of machine breakdown per cycle
NUM_WORKERS = {'loading': 2, 'machining': 3, 'assembling': 4, 'inspecting': 2, 'packaging': 3}
SHIFT_LENGTH = 8  # Hours
SIMULATION_TIME = 100
NUM_PRODUCTS = 2  # Example for multiple product types

class ManufacturingLine:
    def __init__(self, env):
        self.env = env
        # Create resources for each stage
        self.stages = {
            stage: simpy.Resource(env, capacity=NUM_WORKERS[stage]) for stage in NUM_WORKERS
        }
        self.repair_team = simpy.Resource(env, capacity=2)  # Repair team can work on two machines simultaneously
        self.data = []

    def process_part(self, part, product_type):
        stages = ['loading', 'machining', 'assembling', 'inspecting', 'packaging']
        for stage in stages:
            processing_time = PROCESSING_TIMES[stage] * (1 if product_type == 1 else 1.2)  # Adjust time for product type
            with self.stages[stage].request() as request:
                start_time = self.env.now
                yield request
                print(f"{part} entering {stage} at {start_time}")
                try:
                    yield self.env.timeout(processing_time)
                    if random.random() < BREAKDOWN_RATE:
                        yield self.env.process(self.repair_machine(stage))
                    finish_time = self.env.now
                    self.data.append({
                        'Part': part,
                        'Stage': stage,
                        'Start Time': start_time,
                        'Finish Time': finish_time,
                        'Duration': finish_time - start_time,
                        'Product Type': product_type
                    })
                    print(f"{part} leaving {stage} at {finish_time}")
                except simpy.Interrupt:
                    # Handle machine breakdown during processing
                    print(f"{stage} interrupted due to breakdown at {start_time}")
                    yield self.env.process(self.repair_machine(stage))

    def repair_machine(self, stage):
        with self.repair_team.request() as repair:
            start_repair = self.env.now
            yield repair
            yield self.env.timeout(MAINTENANCE_TIME)
            print(f"Repairing {stage} started at {start_repair} and finished at {self.env.now}")

def part_manufacturer(env, line, part_id, product_type):
    print(f"Manufacturing of part {part_id} (Product Type {product_type}) started at {env.now}")
    yield env.process(line.process_part(part_id, product_type))
    print(f"Manufacturing of part {part_id} completed at {env.now}")

def setup(env, num_parts_per_type):
    line = ManufacturingLine(env)
    for product_type in range(1, NUM_PRODUCTS+1):
        for i in range(num_parts_per_type):
            env.process(part_manufacturer(env, line, f"Part_{i+1}", product_type))

    yield env.timeout(SIMULATION_TIME)  # Run simulation for a specific period
    # Convert collected data to DataFrame for analysis
    df = pd.DataFrame(line.data)
    print(df)

# Create a simulation environment
env = simpy.Environment()
# Setup the environment with a number of parts to manufacture
env.process(setup(env, 5))  # Example: 5 parts per product type
# Run the simulation
env.run()

