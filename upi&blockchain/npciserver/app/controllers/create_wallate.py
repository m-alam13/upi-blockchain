from app.models import user_model

def Wallet_create(uuid):
    # id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    balance = Column(Float, default=0.0)
    pin = Column(Integer, nullable=False)
    vpa = Column(String(255), nullable=False)
    user = relationship("User", back_populates="wallet")