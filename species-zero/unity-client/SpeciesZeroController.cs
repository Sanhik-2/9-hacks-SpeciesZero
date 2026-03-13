using System.Collections;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.Networking;

public class SpeciesZeroController : MonoBehaviour
{
    [Header("Network Settings")]
    public string serverUrl = "http://localhost:5000";
    
    [Header("References")]
    public Transform playerTransform;
    public NavMeshAgent agent;
    public Animator animator;
    public MahoragaWheel wheel;
    public ParticleSystem glitchEffect;
    public MeshRenderer aiMeshRenderer;
    public Material ascendedMaterial;
    public Mesh ascendedMesh;

    [Header("AI Stats")]
    public float aiHealth = 100f;
    public float maxHealth = 100f;
    public float playerDamageOutput = 10f;
    public bool isPhase2 = false;
    public bool isSuperArmor = false;
    public bool shadowMode = false;

    private int currentAction = 0;
    private string currentPhenomenon = "none";
    private int turnCount = 0;
    private Queue<int> actionBuffer = new Queue<int>();

    void Start()
    {
        if (agent == null) agent = GetComponent<NavMeshAgent>();
        if (animator == null) animator = GetComponent<Animator>();
        InvokeRepeating(nameof(SensorSweep), 0f, 0.1f);
    }

    void Update()
    {
        if (shadowMode && playerTransform != null)
        {
            Vector3 targetPos = playerTransform.position - playerTransform.forward * 2f;
            agent.SetDestination(Vector3.Lerp(transform.position, targetPos, Time.deltaTime * 1.2f));
        }
    }

    private void SensorSweep()
    {
        if (playerTransform == null) return;

        float distance = Vector3.Distance(transform.position, playerTransform.position);
        Vector3 relativePos = transform.InverseTransformPoint(playerTransform.position);
        float angle = Vector3.Angle(transform.forward, playerTransform.position - transform.position);

        string vertical = transform.position.y > 0.5f ? "Airborne" : "Grounded";
        string velocity = agent.velocity.magnitude > 0.1f ? "Moving" : "Stationary";

        _ = RequestActionAsync(relativePos, vertical, velocity, distance, angle);
    }

    private async Task RequestActionAsync(Vector3 relPos, string vertical, string velocity, float distance, float angle)
    {
        SpeciesState payload = new SpeciesState
        {
            relative_position = new float[] { relPos.x, relPos.y, relPos.z },
            vertical_level = vertical,
            velocity = velocity,
            distance = distance,
            target_angle = angle,
            user_hp = 100f, // Replace with actual player HP
            ai_hp = aiHealth
        };

        string json = JsonUtility.ToJson(payload);
        using (UnityWebRequest req = new UnityWebRequest(serverUrl + "/act", "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");

            var operation = req.SendWebRequest();
            while (!operation.isDone) await Task.Yield();

            if (req.result == UnityWebRequest.Result.Success)
            {
                var response = JsonUtility.FromJson<ActResponse>(req.downloadHandler.text);
                ExecuteAction(response.action);
            }
        }
    }

    private void ExecuteAction(int actionId)
    {
        currentAction = actionId;
        isSuperArmor = false;
        shadowMode = false;

        switch (actionId)
        {
            case 1: // Move Forward
                agent.SetDestination(transform.position + transform.forward * 5f);
                animator.SetTrigger("Walk");
                break;
            case 2: // Lateral Dodge
                Vector3 dodgePos = transform.position + transform.right * (Random.value > 0.5f ? 3f : -3f);
                agent.SetDestination(dodgePos);
                animator.SetTrigger("Dodge");
                break;
            case 7: // Blitz
                isSuperArmor = true; // Stalk movement armor
                agent.speed *= 2f;
                agent.SetDestination(playerTransform.position);
                animator.SetTrigger("Blitz");
                StartCoroutine(ResetSpeed(1f));
                break;
            case 8: // Skirmish
                agent.SetDestination(transform.position + Quaternion.Euler(0, 90, 0) * (transform.position - playerTransform.position).normalized * 5f);
                animator.SetTrigger("Shoot");
                break;
        }
    }

    private IEnumerator ResetSpeed(float delay)
    {
        yield return new WaitForSeconds(delay);
        agent.speed /= 2f;
        isSuperArmor = false;
    }

    public async void TakeDamage(float amount, string phenomenonId)
    {
        if (isSuperArmor) amount *= 0.2f;
        aiHealth -= amount;

        if (aiHealth <= 0 && !isPhase2)
        {
            StartCoroutine(Phase2Transition());
            return;
        }

        await UpdateServer(phenomenonId, amount);
    }

    private async Task UpdateServer(string phenomenonId, float damageTaken)
    {
        SpeciesState payload = new SpeciesState
        {
            action = currentAction,
            phenomenon_id = phenomenonId,
            damage_taken = damageTaken,
            ai_hp = aiHealth,
            turn = turnCount++
        };

        string json = JsonUtility.ToJson(payload);
        using (UnityWebRequest req = new UnityWebRequest(serverUrl + "/update", "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");

            var operation = req.SendWebRequest();
            while (!operation.isDone) await Task.Yield();

            if (req.result == UnityWebRequest.Result.Success)
            {
                var response = JsonUtility.FromJson<UpdateResponse>(req.downloadHandler.text);
                HandleResponseLogic(response);
            }
        }
    }

    private void HandleResponseLogic(UpdateResponse res)
    {
        if (res.identity_suppressed)
        {
            if (glitchEffect != null && !glitchEffect.isPlaying) glitchEffect.Play();
            playerDamageOutput *= 0.5f;
        }
        else
        {
            if (glitchEffect != null) glitchEffect.Stop();
            playerDamageOutput = 10f; // Reset
        }

        if (res.wheel_spin && wheel != null) wheel.TriggerSpin();
        
        // Shadow mode check: if mimicry is high, maybe AI shadows player
        if (res.mockery_flag) shadowMode = true;
    }

    private IEnumerator Phase2Transition()
    {
        isPhase2 = true;
        animator.SetTrigger("Death");
        yield return new WaitForSeconds(2f);

        if (aiMeshRenderer != null)
        {
            aiMeshRenderer.material = ascendedMaterial;
            GetComponent<MeshFilter>().mesh = ascendedMesh;
        }

        aiHealth = maxHealth;
        animator.SetTrigger("Rebirth");
        
        _ = SendRebirthTrigger();
    }

    private async Task SendRebirthTrigger()
    {
        SpeciesState payload = new SpeciesState { rebirth_trigger = true };
        string json = JsonUtility.ToJson(payload);
        using (UnityWebRequest req = new UnityWebRequest(serverUrl + "/update", "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");
            var operation = req.SendWebRequest();
            while (!operation.isDone) await Task.Yield();
        }
    }
}
