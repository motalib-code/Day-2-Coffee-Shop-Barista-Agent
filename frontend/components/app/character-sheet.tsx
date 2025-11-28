import { useWorldState } from '@/hooks/useWorldState';

export function CharacterSheet() {
    const state = useWorldState();

    if (!state || !state.character) return null;

    const { character } = state;

    return (
        <div className="fixed top-20 right-4 z-50 w-64 bg-black/80 text-white p-4 rounded-lg border border-white/20 backdrop-blur-md shadow-lg">
            <h2 className="text-xl font-bold mb-2 text-cyan-400">{character.name}</h2>
            <div className="space-y-2">
                <div className="flex justify-between border-b border-white/10 pb-1">
                    <span className="text-gray-300">HP</span>
                    <span className="font-mono">{character.hp}/{character.max_hp}</span>
                </div>
                <div className="flex justify-between border-b border-white/10 pb-1">
                    <span className="text-gray-300">Status</span>
                    <span className={character.status === 'Healthy' ? 'text-green-400' : 'text-red-400'}>{character.status}</span>
                </div>
                <div>
                    <h3 className="font-semibold mt-2 text-purple-300">Stats</h3>
                    <div className="grid grid-cols-2 gap-1 text-sm text-gray-300">
                        {character.stats && Object.entries(character.stats).map(([key, value]) => (
                            <div key={key} className="capitalize flex justify-between pr-2">
                                <span>{key}</span>
                                <span className="font-mono text-white">{value as any}</span>
                            </div>
                        ))}
                    </div>
                </div>
                <div>
                    <h3 className="font-semibold mt-2 text-yellow-300">Inventory</h3>
                    {character.inventory && character.inventory.length > 0 ? (
                        <ul className="text-sm list-disc list-inside text-gray-300">
                            {character.inventory.map((item: string, i: number) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-sm text-gray-500 italic">Empty</p>
                    )}
                </div>
            </div>
        </div>
    );
}
