using System.Collections;
using UnityEngine;

public class MahoragaWheel : MonoBehaviour
{
    [Header("Wheel Settings")]
    public float spinDuration = 2.0f;
    public float spinSpeed = 360f; // degrees per second
    public AudioClip spinSound;
    private AudioSource audioSource;
    
    private bool isSpinning = false;

    void Start()
    {
        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
        }
    }

    public void TriggerSpin()
    {
        if (!isSpinning)
        {
            StartCoroutine(SpinCoroutine());
        }
    }

    private IEnumerator SpinCoroutine()
    {
        isSpinning = true;
        
        if (spinSound != null)
        {
            audioSource.PlayOneShot(spinSound);
            // Optionally play animation clip: GetComponent<Animator>().SetTrigger("Spin");
        }
        
        float timer = 0f;
        while (timer < spinDuration)
        {
            // Spin the wheel visual clockwise on the Z or Y axis depending on orientation
            transform.Rotate(Vector3.forward, spinSpeed * Time.deltaTime);
            timer += Time.deltaTime;
            yield return null;
        }
        
        // Snap to nice rotation
        transform.eulerAngles = new Vector3(transform.eulerAngles.x, transform.eulerAngles.y, Mathf.Round(transform.eulerAngles.z / 90f) * 90f);
        
        isSpinning = false;
        Debug.Log("Wheel spin complete. Adaptation active.");
    }
}
