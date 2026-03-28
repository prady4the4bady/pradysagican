"""Quick test of integration module"""
import asyncio
from pradysagican.core.integration import initialize_pradysagi, pradysagi

async def test():
    print('Initializing PRADYSAGI Integration...')
    success = await initialize_pradysagi({
        'local_models': True,
        'rag_documents': [
            ('ML is learning from data', 'ML101'),
            ('NNs use layers', 'NN101'),
        ]
    })
    
    if success:
        stats = pradysagi.get_stats()
        print('✅ System initialized!')
        print(f"   RAG docs: {stats['rag_documents']}")
        print(f"   Tools: {stats['tools_available']}")
        print(f"   Mode: {stats['mode']}")
    else:
        print('⚠️ Partial initialization')

if __name__ == "__main__":
    asyncio.run(test())
