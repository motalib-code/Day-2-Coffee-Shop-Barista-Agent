import { useEffect, useState } from 'react';
import { useRoomContext } from '@livekit/components-react';
import { RoomEvent } from 'livekit-client';

export function useWorldState() {
    const room = useRoomContext();
    const [worldState, setWorldState] = useState<any>(null);

    useEffect(() => {
        const onDataReceived = (payload: Uint8Array, participant: any, kind: any, topic?: string) => {
            if (topic === 'world_state') {
                const str = new TextDecoder().decode(payload);
                try {
                    setWorldState(JSON.parse(str));
                } catch (e) {
                    console.error('Failed to parse world state', e);
                }
            }
        };

        room.on(RoomEvent.DataReceived, onDataReceived);
        return () => {
            room.off(RoomEvent.DataReceived, onDataReceived);
        };
    }, [room]);

    return worldState;
}
