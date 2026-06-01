# OLAS Rapid Assessment
## autonolas-registries (Opportunistic)

**Target**: Autonolas Registries  
**Repo**: valory-xyz/autonolas-registries  
**Scope**: ServiceRegistry L1/L2, AgentRegistry, ComponentRegistry, ServiceManager  
**Commit**: Latest (main branch)  
**Time Budget**: 2 hours  

---

## KEY ARCHITECTURE

- **ERC721-based**: Components, Agents, Services are NFTs
- **Manager Pattern**: owner → manager (delegated control)
- **State Machine**: Services have PreRegistration → ActiveRegistration → FinishedRegistration → Deployed → Terminated states
- **Reentrancy Guard**: _locked flag in ServiceRegistry
- **Multisig Integration**: Services deploy as multisigs (Safe, etc.)
- **Access Control**: Manager checks on all write functions

---

## ATTACK SURFACE

1. **Access Control**: Manager/Owner modifiers on write functions
2. **State Lifecycle**: Service state transitions and invariants
3. **ID Lifecycle**: Register → Update → Deregister → Reuse?
4. **Stale References**: After deregister, getters/resolvers behavior
5. **Fee/Deposit Mechanics**: Security deposit, slashing
6. **Cross-Registry**: Agent/Component dependency tracking

---

## THREAT VECTORS (HIGH-PROBABILITY)

**TV-B: Access Control Bypass**  
- Source: S5 (Access Control Edges)  
- Hypothesis: Manager checks incomplete or bypassable; create/update/deploy callable by non-manager
- Target: create, update, activateRegistration, registerAgents, deploy, terminate, unbond
- Critical functions: All write functions in ServiceRegistry

**TV-A: ID Lifecycle Flaw**  
- Source: S1 (State Transitions)  
- Hypothesis: Register → Deregister → Re-register with same ID; state overwrites or ID reuse
- Target: ServiceRegistry.create, update, terminate
- Critical: mapServices[serviceId] state persistence after termination

**TV-F: Stale Reference After Deregister**  
- Source: S1 (State Transitions)  
- Hypothesis: After service deregister/terminate, getService/ownerOf resolvers return stale data or don't revert
- Target: getService, ownerOf, getAgentInstances
- Critical: Consumers relying on terminated service data

---

## SUCCESS CRITERIA

- **PASS**: All 3 TVs show proper revert or explicit inactive flag
- **FAIL**: Any write function callable by non-authorized; ID can be reused; stale reference resolution succeeds
