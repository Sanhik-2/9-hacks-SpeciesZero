using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

public class SpeciesController : MonoBehaviour
{
    [Header("Server Settings")]
    public string serverUrl = "http://localhost:5000";
    
    [Header("Agent State")]
    public string currentState = "0";
    public int currentAction = 0;
    
    [Header("References")]
    public MahoragaWheel wheel;
    
    // Call this method when you want the AI to act
    public void RequestAction(string phenomenonId)
    {
        StartCoroutine(ActCoroutine(phenomenonId));
    }
    
    private IEnumerator ActCoroutine(string phenomenonId)
    {
        SpeciesState payload = new SpeciesState
        {
            state = currentState,
            phenomenon_id = phenomenonId,
            damage_taken = 0f,
            damage_to_player = 0f
        };
        
        string json = JsonUtility.ToJson(payload);
        
        using (UnityWebRequest req = new UnityWebRequest(serverUrl + "/act", "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");
            
            yield return req.SendWebRequest();
            
            if (req.result == UnityWebRequest.Result.Success)
            {
                var response = JsonUtility.FromJson<ActResponse>(req.downloadHandler.text);
                if (string.IsNullOrEmpty(response.error))
                {
                    currentAction = response.action;
                    ExecuteAction(currentAction);
                }
                else
                {
                    Debug.LogError("Server Error: " + response.error);
                }
            }
            else
            {
                Debug.LogError("Error connecting to RL Server: " + req.error);
            }
        }
    }
    
    private void ExecuteAction(int actionIndex)
    {
        Debug.Log("Executing chosen action: " + actionIndex);
        switch(actionIndex)
        {
            case 0: // Idle
                break;
            case 1: // Chase
                transform.Translate(Vector3.forward * 2f);
                break;
            case 2: // Dodge
                transform.Translate(Vector3.right * 2f);
                break;
            case 3: // Attack
                // Logic to deal damage back to the player goes here in your game
                break;
        }
    }
    
    // Call this when the agent takes damage and optionally deals damage
    public void RecordDamageAndUpdate(string phenomenonId, float damageTaken, float damageToPlayer, float aiHp, float userHp, bool isPlayerDead, string nextState)
    {
        StartCoroutine(UpdateCoroutine(phenomenonId, damageTaken, damageToPlayer, aiHp, userHp, isPlayerDead, nextState));
    }
    
    private IEnumerator UpdateCoroutine(string phenomenonId, float damageTaken, float damageToPlayer, float aiHp, float userHp, bool isPlayerDead, string nextState)
    {
        SpeciesState payload = new SpeciesState
        {
            state = currentState,
            action = currentAction,
            next_state = nextState,
            phenomenon_id = phenomenonId,
            damage_taken = damageTaken,
            damage_to_player = damageToPlayer,
            ai_hp = aiHp,
            user_hp = userHp,
            is_player_dead = isPlayerDead
        };
        
        string json = JsonUtility.ToJson(payload);
        
        using (UnityWebRequest req = new UnityWebRequest(serverUrl + "/update", "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");
            
            yield return req.SendWebRequest();
            
            if (req.result == UnityWebRequest.Result.Success)
            {
                var response = JsonUtility.FromJson<UpdateResponse>(req.downloadHandler.text);
                
                if (response.wheel_spin)
                {
                    Debug.Log("MAHORAGA ADAPTATION TRIGGERED!");
                    if (wheel != null)
                    {
                        wheel.TriggerSpin();
                    }
                }
                
                currentState = nextState;
            }
            else
            {
                Debug.LogError("Error updating RL Server: " + req.error);
            }
        }
    }
}
