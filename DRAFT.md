
```python

class TaskStateMachine(StateMachine):
    def __init__(self, task_id: str) -> Self:
        self._task_id = task_id
        # storage
        # lock

        states

    @st.iniitial
    def handle(self, ):

        self.switch()

    @pre_state(all=True):
    def pre_state():
        pass

    @post_state
    def post_state(self, )
        pass

```

Middlewares for events: prestates, save

state/
inject/
store/

Inspiration:
- https://github.com/fgmacedo/python-statemachine
