/**
 * Minimal WHEP (WebRTC-HTTP Egress Protocol) client.
 *
 * Sends an SDP offer to the gateway (which authorizes + proxies to MediaMTX),
 * applies the answer, and surfaces the remote media stream. Media (ICE/RTP)
 * flows directly between the browser and MediaMTX; only signaling goes through
 * the gateway.
 */

export interface WhepSession {
  pc: RTCPeerConnection;
  close: () => Promise<void>;
}

export async function connectWhep(
  whepUrl: string,
  token: string,
  onTrack: (stream: MediaStream) => void,
  onConnectionState: (state: RTCPeerConnectionState) => void,
): Promise<WhepSession> {
  const pc = new RTCPeerConnection({
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
  });

  pc.addTransceiver('video', { direction: 'recvonly' });
  pc.addTransceiver('audio', { direction: 'recvonly' });

  pc.ontrack = (event) => {
    if (event.streams[0]) onTrack(event.streams[0]);
  };
  pc.onconnectionstatechange = () => onConnectionState(pc.connectionState);

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  const res = await fetch(whepUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/sdp', Authorization: `Bearer ${token}` },
    body: offer.sdp,
  });
  if (!res.ok) {
    pc.close();
    throw new Error(`WHEP negotiation failed (${res.status})`);
  }

  const answer = await res.text();
  const resourceLocation = res.headers.get('Location');
  await pc.setRemoteDescription({ type: 'answer', sdp: answer });

  const close = async () => {
    try {
      if (resourceLocation) {
        // Resolve relative to the WHEP endpoint origin.
        const url = new URL(resourceLocation, whepUrl);
        await fetch(url.toString(), { method: 'DELETE' }).catch(() => undefined);
      }
    } finally {
      pc.close();
    }
  };

  return { pc, close };
}
